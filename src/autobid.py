import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import argparse
import json
import logging
from collections import Counter, defaultdict
from multiprocessing import Pool, cpu_count
from pathlib import Path

import numpy as np
from gensim import corpora
from gensim.models.ldamodel import LdaModel
from tqdm import tqdm

from utils.pdf_utils import analyze_words

logger = logging.getLogger(__name__)

class AutoBid:

    def __init__(self, model_dir, corpus_dir=None, no_topics=50, workers=1, lazy=False):
        self.model_dir = model_dir
        self.lazy = lazy
        self.no_topics = no_topics
        self.workers = workers

        # Step 0: check model
        if corpus_dir is None and \
           (not model_dir.joinpath('lda.model').is_file() or \
            not model_dir.joinpath('reviewer_topics.json').is_file()or \
            not model_dir.joinpath('reviewer_to_words_mapping.json').is_file()):
           raise ValueError(f"Model {model_dir} is not trained")

        # Step 1: LDA model
        model_dir.mkdir(exist_ok=True, parents=True)
        model_cache = model_dir.joinpath('lda.model')
        if not model_cache.is_file():
            if corpus_dir is None:
                raise ValueError("Could not found a corpus for Training")
            # a. load corpus
            corpus_cache = corpus_dir.joinpath('corpus.json')
            if not corpus_cache.is_file():
                # find all PDFs in corpus dir
                # => duplicates are excluded via the PDF names
                pdf_files = list({ pdf.name : pdf for pdf in corpus_dir.rglob('*.pdf') }.values())
                with Pool(self.workers) as p:
                    words_per_pdf = p.imap(analyze_words, pdf_files, chunksize=32)
                    corpus = [ words for words in tqdm(words_per_pdf, total=len(pdf_files), bar_format='    {l_bar}{bar:30}{r_bar}') ]
                corpus_cache.write_text(json.dumps(corpus))
            corpus = json.loads(corpus_cache.read_text())
            # b. encode corpus with id <-> term dictionary
            id2word = corpora.Dictionary(corpus)
            corpus = [id2word.doc2bow(text) for text in corpus]
            # c. train model
            ldamodel = LdaModel(corpus, num_topics=self.no_topics, iterations=50, id2word=id2word, passes=30)
            ldamodel.save(model_cache.as_posix())
        # load model
        if not lazy:
            # lazily load model to reduce memory load
            self.model = LdaModel.load(model_cache.as_posix())

        # Step 2: Reviewers
        reviewers_to_topics_cache = model_dir.joinpath('reviewer_topics.json')
        if not reviewers_to_topics_cache.is_file():
            # a. load reviewer archives
            reviewers_archives_cache = corpus_dir.joinpath('archives').joinpath('reviewer_archives.json')
            if not reviewers_archives_cache.is_file():
                reviewers = {}
                reviewer_archives_dirs = [ d for d in corpus_dir.joinpath('archives').glob("*") if d.is_dir()]
                with Pool(self.workers) as p:
                    reviewers_archives = p.imap(self._load_reviewer_archive, reviewer_archives_dirs)
                    for reviewer_dir, reviewers_archive in tqdm(zip(reviewer_archives_dirs, reviewers_archives), 
                                                                    total=len(reviewer_archives_dirs),
                                                                    bar_format='    {l_bar}{bar:30}{r_bar}'):    
                        reviewer_name = reviewer_dir.name
                        reviewers[reviewer_name] = reviewers_archive
                reviewers_archives_cache.write_text(json.dumps(reviewers))
            reviewers = json.loads(reviewers_archives_cache.read_text())
            # b. get topics
            reviewers_to_topics = []
            for reviewer_name, reviewer_words in reviewers.items():
                reviewer_topics = self.get_topics(reviewer_words)
                reviewers_to_topics += [ (reviewer_name, reviewer_topics.tolist()) ]
            reviewers_to_topics_cache.write_text(json.dumps(reviewers_to_topics, indent=4))
        # load reviewers topics
        reviewers_to_topics = json.loads(reviewers_to_topics_cache.read_text())
        self.reviewers_list, self.reviewers_topics = zip(*reviewers_to_topics)
        self.reviewers_topics = [ np.asarray(topics) for topics in self.reviewers_topics]

        # Step 3: Map reviewer to words
        reviewer_to_words_cache = model_dir.joinpath('reviewer_to_words_mapping.json')
        if not reviewer_to_words_cache.is_file():
            with Pool(self.workers) as p:
                reviewer_idxes = list(range(len(self.reviewers_list)))
                reviewer_to_words_mapping = list(tqdm(p.imap(self._map_reviewer_words, reviewer_idxes), ncols=80, total=len(reviewer_idxes)))

            # dump
            reviewer_to_words_cache.write_text(json.dumps(reviewer_to_words_mapping, indent=4))

    def __repr__(self):
        return f'AutoBid <{self.model_dir}>'

    def get_topics(self, words):
        if self.lazy:
            model = LdaModel.load(self.model_dir.joinpath('lda.model').as_posix())
            topics = model[model.id2word.doc2bow(words)]
        else:
            topics = self.model[self.model.id2word.doc2bow(words)]
        topic_probabilities = [0]*self.no_topics
        for topic in topics:
            topic_probabilities[topic[0]] = topic[1]
        return np.array(topic_probabilities)

    def get_reviewer(self, reviewer_name):
        reviewer_idx = self.reviewers_list.index(reviewer_name)
        topics = self.reviewers_topics[reviewer_idx]
        return reviewer_idx, topics
    
    def get_scores(self, submission_words, normalized=True):
        submission_topics = self.get_topics(submission_words)
        scores = [ reviewer_topics.dot(submission_topics) for reviewer_topics in self.reviewers_topics ]
        if not normalized:
            return scores
        score_max = np.amax(scores)
        score_min = np.amin(scores)
        normalized_scores = (scores - score_min) / float(score_max - score_min)
        return normalized_scores

    def get_ranking(self, thingy):
        # submission words
        # => either path to PDF
        if isinstance(thingy, Path):
            if not thingy.is_file():
                raise ValueError(f"Could not find submission {thingy}")
            submission_words = self.parse_pdf_file(thingy)
        # => or list of words
        elif isinstance(thingy, list):
            submission_words = thingy
        else:
            raise ValueError(thingy)
        # ranking
        return sorted(zip(self.reviewers_list, self.get_scores(submission_words)), key=lambda x: x[1], reverse=True)

    @staticmethod
    def parse_pdf_file(pdf):
        return analyze_words(pdf)

    def _load_reviewer_archive(self, reviewer_dir):
        count = Counter()
        words = []
        for pdf_file in reviewer_dir.glob('*.pdf'):
            pdf_words = analyze_words(pdf_file)
            count.update(pdf_words)
            words += pdf_words
        return words

    def _map_reviewer_words(self, reviewer_idx):
        # get topic vector
        reviewer_topics = self.reviewers_topics[reviewer_idx]
        # get words for each topic
        reviewer_words = defaultdict(list)
        for idx, topic_prob in enumerate(reviewer_topics):
            if topic_prob == 0:
                continue
            for word_id, word_prob in  self.model.get_topic_terms(idx, topn=int(1e6)):
                word = self.model.id2word[word_id]
                reviewer_words[word] += [ word_prob*topic_prob ]
        # aggregate
        reviewer_words = [ (w, np.mean(p)) for w, p in reviewer_words.items() ]
        # save the 5000 with highest probability
        topn = list(sorted(reviewer_words, key=lambda x: x[1], reverse=True))[:5000]
        return topn

    def __hash__(self):
        return hash(self.model_dir.as_posix())

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus_dir', type=Path)
    parser.add_argument('--models_dir', type=Path, default=None)
    parser.add_argument('--no_models', default=8, type=int)
    parser.add_argument('--no_topics', default=50, type=int)
    parser.add_argument('--passes', default=30, type=int)
    parser.add_argument('--iterations', default=50, type=int)
    parser.add_argument('--workers', default=1, type=int)
    args = parser.parse_args()

    print(f'[+] Arguments')
    print(args.corpus_dir)
    print(args.no_topics)
    print(args.passes)
    print(args.iterations)
    print(args.no_models)
    print(args.workers)
    
    if args.models_dir is None:
        models_dir = Path.home().joinpath('adversarial-papers', 'evaluation', 'models', f'{args.corpus_dir.name}', f'{model_idx:>02}')
    else:
        assert args.no_models == 1
        models_dir = args.models_dir

    logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    for model_idx in tqdm(range(args.no_models), ncols=80):
        AutoBid(model_dir=models_dir, corpus_dir=args.corpus_dir, workers=args.workers)
