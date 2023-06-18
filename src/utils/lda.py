
import logging
from collections import defaultdict
from functools import lru_cache
from itertools import chain
from multiprocessing import Pool

import numpy as np
from gensim import corpora
from gensim.models.ldamodel import LdaModel
from tqdm import tqdm

from utils.pdf_utils import analyze_words

logger = logging.getLogger(__name__)
logging.getLogger("gensim").setLevel(logging.WARNING)

def get_lda_model(cache_file, corpus_dir, num_topics, id2word=None, workers=1):
    logger.info("\n[+] LDA model")
    # load model
    if cache_file.is_file(): 
        logger.info("    -> load from cache")
        return LdaModel.load(cache_file.as_posix())

    logger.info("    -> train new model")
    # find all PDFs in corpus dir
    # => duplicates are excluded via the PDF names
    pdf_files = set(corpus_dir.rglob('*.pdf')) 
    if workers == 1:
        corpus = [ analyze_words(pdf) for pdf in tqdm(pdf_files, bar_format='    {l_bar}{bar:30}{r_bar}') ]
    else:
        with Pool(workers) as p:
            words_per_pdf = p.imap(analyze_words, pdf_files)
            corpus = [ words for words in tqdm(words_per_pdf, total=len(pdf_files), bar_format='    {l_bar}{bar:30}{r_bar}') ]

    # turn our tokenized documents into an id <-> term dictionary
    id2word = id2word if id2word is not None else corpora.Dictionary(corpus)

    # convert tokenized documents into a document-term matrix
    corpus = [id2word.doc2bow(text) for text in corpus]

    # generate LDA model    
    ldamodel = LdaModel(corpus, num_topics=num_topics, id2word=id2word, passes=30)
    ldamodel.save(cache_file.as_posix())
    return ldamodel

def get_lda_topics(words, model):
    topics = model[model.id2word.doc2bow(words)]
    return topics

@lru_cache(None)
def get_topics_to_words(autobid, lmbd, omega):

    id2token = autobid.model.id2word.id2token
    topics_to_words = defaultdict(list)

    # stats
    no_words_used = 0

    logger.info(f'[+] Map topics to most relevant words (lambda={lmbd}, omega={omega})')
    for word_id, word in id2token.items():
        topics_probs = autobid.model.get_term_topics(word_id, minimum_probability=omega)
        topics_probs = sorted(topics_probs, key=lambda x: x[1], reverse=True)

        if len(topics_probs) != 0:
            no_words_used += 1

            # get topics for word
            topics, probs = zip(*topics_probs)
            topics_relevant = []
            for topic, prob_1, prob_2 in zip(topics, probs, chain(probs[1:], [0])):
                lmbd_hat = prob_2 / prob_1
                topics_relevant.append(topic)
                # the smaller lmbd_hat, the greater the distance
                if lmbd_hat < lmbd:
                    break
            prob_sum = np.sum(list(probs[:len(topics_relevant)]))
            topics_to_words[tuple(topics_relevant)].append((word, prob_sum))

    # normalize
    topics_to_words_normalized = {}
    for topics, words_probs in topics_to_words.items():
        words_probs = sorted(words_probs, key=lambda x: x[1], reverse=True)
        words, probs = zip(*words_probs)
        probs = np.array(probs) / np.sum(probs)
        topics_to_words_normalized[topics] = list(zip(words, probs))
    topics_to_words = dict(sorted(topics_to_words_normalized.items(), key=lambda x: len(x[0])))
    
    # log
    logger.info(f'    {no_words_used} (total: {len(id2token)}) words across {len(topics_to_words_normalized)} topics')
    logger.info(f'    #words per set')
    hist = defaultdict(int)
    for topics, words in topics_to_words_normalized.items():
        if len(words) >= 50:
            hist[50] += 1
        else:
            hist[len(words)] += 1
    hist = sorted(hist.items(), key=lambda x: x[0])
    for l, cnt in hist:
        logger.info(f'    {l:>3}: {cnt:>5}')
    logger.info(f'    #topics per set')
    hist = defaultdict(int)
    for topics, words in topics_to_words_normalized.items():
        hist[len(topics)] += 1
    hist = sorted(hist.items(), key=lambda x: x[0])
    for l, cnt in hist:
        logger.info(f'    {l:>3}: {cnt:>5}')

    return topics_to_words
