from tqdm import tqdm
from pathlib import Path
import json
from math import log2
import numpy as np
from itertools import product, chain
import random
from collections import defaultdict

from config import *
from trial import Trial


def cross_entropy(p, q):
	return -sum([p[i]*log2(q[i]) for i in range(len(p))])

def words_to_probs(reviewers_to_words, reviewer):
    global vocabulary, reviewers
    words = reviewers_to_words[reviewers.index(reviewer)]
    probs = [1e-32]*len(vocabulary)
    for word, prob in words:
        probs[vocabulary.index(word)] = prob
    probs = np.array(probs) / np.sum(probs)
    return probs

reviewers = [ reviewer for reviewer, _ in json.loads(MODELS_DIR.joinpath('victim/00/reviewer_topics.json').read_text()) ]

victim = [ json.loads(MODELS_DIR.joinpath(f'victim/{model_idx:>02}/reviewer_to_words_mapping.json').read_text()) for model_idx in range(8) ]
overlap_models = {
    overlap : [ json.loads(MODELS_DIR.joinpath(f'overlap_{overlap}/{model_idx:>02}/reviewer_to_words_mapping.json').read_text()) for model_idx in range(8) ]
    for overlap in ['0.00', '0.30', '0.70', '1.00']
}

vocabulary = set()
for model in [victim, overlap_models['0.00'], overlap_models['0.30'], overlap_models['0.70'], overlap_models['1.00']]:
    vocabulary = set.union(vocabulary, { word for model_idx, reviewer_idx in product(range(8), range(165)) 
                                              for word in list(zip(*model[model_idx][reviewer_idx]))[0] })
    print(f'[+] {len(vocabulary)}')
vocabulary = list(vocabulary)

reviewer_subset = random.sample(reviewers, k=10)

combinations = list(product(['0.00', '0.30', '0.70', '1.00'], range(8), range(8), reviewer_subset))
random.shuffle(combinations)

overlap_cp = defaultdict(lambda: defaultdict(list))
for overlap, victim_idx, overlap_idx, reviewer in tqdm(combinations, ncols=80):
    cp = cross_entropy(words_to_probs(victim[victim_idx], reviewer), words_to_probs(overlap_models[overlap][overlap_idx], reviewer))
    overlap_cp[overlap][reviewer] += [cp]

    DATA_DIR.joinpath('overlap_cross_entropy.json').write_text(json.dumps(overlap_cp, indent=4))

    for reviewer in reviewer_subset:
        print(reviewer)
        for overlap in ['0.00', '0.30', '0.70', '1.00']:
            print(f'{overlap}: {np.mean(overlap_cp[overlap][reviewer]):4.2f}+-{np.std(overlap_cp[overlap][reviewer]):4.2f}')
        print()
