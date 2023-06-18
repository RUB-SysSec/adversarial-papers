import nltk
import yaml
import re
import os
import gzip
import sys
import json
import itertools

from functools import partial
from multiprocessing import Pool
from tqdm import tqdm


def load_config(cfg_file, obj):
    """ Load config and attach to obj """

    def gen_attrs(d, attrs=[], path=""):
        """ Helper function for nested parameters """
        for k, v in d.items():
            if isinstance(v, dict):
                gen_attrs(v, attrs, "%s%s_" % (path, k))
            else:
                attrs.append(("%s%s" % (path, k), v))
        return attrs

    with open(cfg_file) as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

    for key, val in gen_attrs(cfg):
        if not hasattr(obj, key) or not getattr(obj, key):
            setattr(obj, key, val)

    return cfg


def progress_map(func, jobs, desc=None):
    """ Unordered multi-threading map with progress bar """
    pool = Pool()
    result = []
    for x in tqdm(pool.imap(func, jobs), total=len(jobs), desc=desc):
        result.append(x)
    return result


def load_data(data_file):
    """ Load text corpus """

    if data_file.endswith(".txt.gz"):
        # Raw gzipped text
        with gzip.open(data_file, 'rt', encoding="utf-8") as f:
            data = f.read()
    elif data_file.endswith(".txt"):
        # Raw text
        with open(data_file, 'rt', encoding="utf-8") as f:
            data = f.read()
    elif data_file.endswith(".json"):
        # Dictionary, values are text
        with open(data_file, 'rt', encoding="utf-8") as f:
            papers = json.load(f)
        data = ' '.join(papers.values())

    # Replace non-ascii symbols
    data = ''.join([i if ord(i) < 128 else ' ' for i in data])
    return data


def clean_data(data):
    """ Clean raw data """

    replace_strs = [
        ("Fig.", "Figure"), ("Tab.", "Table"),  # Fix abbreviations
        ("Eq.", "Equation"), ("Sect.", "Section"),
        ("Def.", "Definition"),
        (" ,", ","), (" .", "."), ("``", ""),  # Fix some punctation
        ("\"", ""), ("''", ""), ("`", "'"),
        ("\x03", " ")  # Left characters
    ]
    for x, y in replace_strs:
        data = data.replace(x, y)

    replace_regex = [
        (r"https?://\S+", "<url>"),  # URLs
        (r"\[\d+\]", ""),  # Citations
        (r"\d+", "<num>"),  # Numbers-alike
        (r"\.+", ".")  # Multiple dots
    ]
    for x, y in replace_regex:
        data = re.sub(x, y, data)

    return data

def fix_punctation(chunk):
    """ Fix broken punctation in chunk """
    for i, sent in enumerate(chunk):
        chunk[i] = re.sub(r"\.+", " . ", sent)
    return chunk

def word_tokenize(tokenizer, chunk):
    for i, sent in enumerate(chunk):
        chunk[i] = tokenizer.tokenize(sent)
    return chunk

def filter_sentences(args, chunk):
    """ Filter small sentences from chunk """
    chunk = [s for s in chunk if len(s) >= args.nltk_min_tokens]
    return chunk

def stem_tokens(stemmer, chunk):
    """ Stem tokens """
    chunk = [[stemmer.stem(t) for t in s] for s in chunk]
    return chunk
    
def lower_tokens(chunk):    
    """ Lower-case tokens """
    chunk = [[t.lower() for t in s] for s in chunk]
    return chunk

def nltk_process(data, args):
    """ Process with NLTK: sentences, tokenize and stem"""
    # Prepare sentence parser
    home_dir = os.getenv("HOME")
    nltk.download('punkt', download_dir='%s/.nltk' % home_dir, quiet=True)
    word_tok = nltk.tokenize.TreebankWordTokenizer()
    stemmer = nltk.stem.PorterStemmer()

    # Split by paragraph
    chunks = data.split('\n\n')

    # Tokenize sentences 
    func = nltk.sent_tokenize
    chunks = progress_map(func, chunks, desc="sent_tokenize")

    # Fix puncations
    func = fix_punctation
    chunks = progress_map(func, chunks, desc="fix_punctation")

    # Tokenize words
    func = partial(word_tokenize, word_tok)
    chunks = progress_map(func, chunks, desc="word_tokenize")

    # Filter sentences
    func = partial(filter_sentences, args)
    chunks = progress_map(func, chunks, desc="filter_sentences")

    # Stem tokens in sentences
    if args.nltk_stemming:
       func = partial(stem_tokens, stemmer) 
       chunks =  progress_map(func, chunks, desc="stem_tokens")

    # Convert to lowercase
    if args.nltk_lower:
        func = lower_tokens
        chunks = progress_map(func, chunks, desc="lower_tokens")
        
    data = list(itertools.chain.from_iterable(chunks))
    return data

def error(msg, code=-1):
    """ Simple error message """
    print("Error: %s" % msg)
    sys.exit(code)
