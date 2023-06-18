import sys
from pathlib import Path
sys.path.append(Path.home().joinpath('adversarial-papers', 'src').as_posix())  

import json
import random
import shutil
from collections import defaultdict
from itertools import chain, combinations

import numpy as np
from autobid import AutoBid
from problemspace.PdfLatexSource import PdfLatexSource
from tqdm import tqdm

MODELS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'models')
TARGETS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'targets')

targets_dir = TARGETS_BASE_DIR / "surrogates"
targets_dir.mkdir(parents=True, exist_ok=True)

no_models = 8
no_targets = 100 

random.seed(2022)

whitebox_targets = json.loads(Path.home().joinpath("adversarial-papers/evaluation/targets2/featurespace-search.json").read_text())

overlap_models = defaultdict(list)
for overlap_model in sorted([ model_dir.parent for model_dir in MODELS_BASE_DIR.glob('overlap_*/*/reviewer_topics.json') ]):
    overlap = overlap_model.parent.name.split('_')[1]
    overlap_models[overlap] += [ overlap_model ]
overlap_models = dict(sorted(overlap_models.items(), key=lambda x: x[0]))

configs = []
for no_surrogates in [1, 2, 4, 8, 3, 5, 6, 7]:
    configs = []
    for target in whitebox_targets:
        surrogate_models = random.sample(overlap_models['0.70'], k=no_surrogates)
        configs += [{
            'submission' : target['submission'],
            'target_reviewer' : target['target_reviewer'],
            'victim_models' : target['victim_models'],
            'surrogate_models' : [ f'{model_dir.relative_to(MODELS_BASE_DIR).as_posix()}' for model_dir in surrogate_models ]
        }]

    targets_dir.joinpath(f'surrogate_targets_{no_surrogates}.json').write_text(json.dumps(configs, indent=4))
