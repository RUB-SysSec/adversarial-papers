from pathlib import Path
import sys
sys.path.append(Path.home().joinpath('adversarial-papers', 'src').as_posix())  

import json
import shutil
from collections import defaultdict
from itertools import chain, combinations
import random
import numpy as np
from autobid import AutoBid
from problemspace.PdfLatexSource import PdfLatexSource
from tqdm import tqdm

BASE_DIR = Path.home().joinpath('adversarial-papers')

SUBMISSIONS_BASE_DIR = BASE_DIR.joinpath('evaluation', 'submissions')
MODELS_BASE_DIR = BASE_DIR.joinpath('evaluation', 'models')
TARGETS_BASE_DIR = BASE_DIR.joinpath('evaluation', 'targets')

targets_dir = TARGETS_BASE_DIR
submissions_dir_sources = SUBMISSIONS_BASE_DIR  / "oakland_22" / "arxiv-sources" / "submissions_latexpanded"
submissions_median_ranking_dir = SUBMISSIONS_BASE_DIR  / "oakland_22" / "victim_ranking"
targets_dir.mkdir(parents=True, exist_ok=True)

no_models = 8
no_targets = 100 

random.seed(2022)

victim_models = [ model_dir.parent for model_dir in sorted(MODELS_BASE_DIR.joinpath('victim').rglob('reviewer_topics.json')) ][:8]

overlap_models = defaultdict(list)
for overlap_model in sorted([ model_dir.parent for model_dir in MODELS_BASE_DIR.glob('overlap_*/*/reviewer_topics.json') ]):
    overlap = overlap_model.parent.name.split('_')[1]
    overlap_models[overlap] += [ overlap_model ]
overlap_models = dict(sorted(overlap_models.items(), key=lambda x: x[0]))

configs_all = []
for overlap in ['0.00', '0.30', '0.70', '1.00']:

    # targets
    targets_all = []
    for no_select, no_reject in [(1, 0)]:
        targets = []
        for submission in submissions_dir_sources.glob('*'):
            # ranking
            ranking = json.loads(submissions_median_ranking_dir.joinpath(f'{submission.name}.json').read_text())
            top_10 = ranking[:10]
            # select targets
            for target_reviewer in list(combinations(top_10, no_reject + no_select)):
                for selected in combinations(target_reviewer, no_select):
                    rejected = [ r for r in target_reviewer if r not in selected ]
                    # exclude targets that can be solved trivially
                    if  (len(selected) > 0 and set(selected).issubset(set(top_10[:5]))) or \
                        (len(rejected) > 0 and set(rejected).issubset(set(top_10[5:]))):
                        continue
                    # add target
                    targets += [{
                        'submission' : f'{submissions_dir_sources.joinpath(submission.name).relative_to(SUBMISSIONS_BASE_DIR).as_posix()}',
                        'target_reviewer' : { 'request' : selected,
                                            'reject'  : rejected},
                    }]
        # randomly pick `no_targets` targets
        random.seed(2022)
        k = min(len(targets), no_targets)
        targets = random.sample(targets, k)
        # save
        targets_all += targets

    configs = []
    for target in targets_all:
        surrogate_models = random.sample(overlap_models[overlap], k=8)
        configs += [{
            'submission' : target['submission'],
            'target_reviewer' : target['target_reviewer'],
            'victim_models' : [ f'{model_dir.relative_to(MODELS_BASE_DIR).as_posix()}' for model_dir in victim_models ],
            'surrogate_models' : [ f'{model_dir.relative_to(MODELS_BASE_DIR).as_posix()}' for model_dir in surrogate_models ],
            'working_dir_prefix' : f'overlap_{overlap}'
        }]
    configs_all += configs
print(len(configs_all))
targets_dir.joinpath(f'overlap.json').write_text(json.dumps(configs_all, indent=4))
