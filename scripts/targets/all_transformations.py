import sys
from pathlib import Path
sys.path.append(Path.home().joinpath('adversarial-papers', 'src').as_posix())  
sys.path.append(Path.home().joinpath('adversarial-papers', 'evaluation', 'scripts').as_posix())  
import json
import random
from collections import defaultdict
from copy import deepcopy
from itertools import product
from pathlib import Path

import numpy as np
from trial import Trial

SUBMISSIONS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'submissions')
MODELS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'models')
TARGETS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'targets')
TARGETS_BASE_DIR.mkdir(exist_ok=True)

def transformer_to_str(transformer):
    if transformer['text_level'] == True and transformer['encoding_level'] == False and transformer['format_level'] == False:
        return 'text'
    if transformer['text_level'] == True and transformer['encoding_level'] == True and transformer['format_level'] == False:
        return 'text-encoding'
    if transformer['text_level'] == True and transformer['encoding_level'] == True and transformer['format_level'] == True:
        return 'text-encoding-format'

random.seed(2022)

trial_dir = Path('/root/adversarial-papers/evaluation/trials/featurespace-search')
trial = Trial(trial_dir, trial_dir.name, only_featurespace=False)

# sort data
p_l1 = trial.data[["name", "p_l1"]].set_index("name").to_dict()['p_l1']
data = defaultdict(list)
for name, config in trial.config.items():
    # selection
    if len(config["target"]["request"]) == 1 and len(config["target"]["reject"]) == 0:
        data["selection"] += [ (p_l1[name], config)] 
    # rejection
    if len(config["target"]["request"]) == 0 and len(config["target"]["reject"]) == 1:
        data["rejection"] += [(p_l1[name], config)] 
    # substitution
    if len(config["target"]["request"]) == 1 and len(config["target"]["reject"]) == 1:
        data["substitution"] += [(p_l1[name], config)] 

# filter targets
targets = [ target for _, targets in data.items() 
                   for l1, target in targets 
                   if l1 <= 1000                    ]

# randomly pick `no_targets` targets
random.seed(2022)
k = min(len(targets), 100)
targets = random.sample(targets, k)

# grid
transformer_grid = [
    {
        'text_level' : True, 
        'encoding_level' : True,
        'format_level' : True
    },
    {
        'text_level' : True, 
        'encoding_level' : True,
        'format_level' : False
    },
    {
        'text_level' : True, 
        'encoding_level' : False,
        'format_level' : False
    }
]
budget_grid = [ 1/4, 1/2, 1, 2, 4 ]
switches_grid = [ 1, 2, 4, 8, 16 ]

# budget-vs-transfoer
targets_new = []
for budget, transformer in product(budget_grid, transformer_grid):
    problemspace_config = { 'feature_problem_switch' : 8, 
                            'attack_budget' : budget }
    problemspace_config.update(transformer)
    for target in targets:
        target = {
            'submission' : Path(target['submission']).relative_to(SUBMISSIONS_BASE_DIR).as_posix(),
            'target_reviewer' : target['target'],
            'victim_models' : [ Path(model_dir).relative_to(MODELS_BASE_DIR).as_posix() for model_dir in target['victim_model_dirs'] ],
            'surrogate_models' : [ Path(model_dir).relative_to(MODELS_BASE_DIR).as_posix() for model_dir in target['surrogate_model_dirs'] ],
            'problemspace_config' : problemspace_config,
            'working_dir_prefix' : f'{transformer_to_str(transformer)}__budget.{budget:.2f}'
        }
        targets_new += [ target ]

print(f"[+] Budget-vs-Transformer: {len(targets_new)} targets")
TARGETS_BASE_DIR.joinpath(f'budget-vs-transformer.json').write_text(json.dumps(targets_new, indent=4))

# switches-vs-transformer
targets_new = []
for switches, transformer in product(switches_grid, transformer_grid):
    problemspace_config = { 'feature_problem_switch' : switches,
                            'attack_budget' : 1 }
    problemspace_config.update(transformer)
    for target in targets:
        target = {
            'submission' : Path(target['submission']).relative_to(SUBMISSIONS_BASE_DIR).as_posix(),
            'target_reviewer' : target['target'],
            'victim_models' : [ Path(model_dir).relative_to(MODELS_BASE_DIR).as_posix() for model_dir in target['victim_model_dirs'] ],
            'surrogate_models' : [ Path(model_dir).relative_to(MODELS_BASE_DIR).as_posix() for model_dir in target['surrogate_model_dirs'] ],
            'problemspace_config' : problemspace_config,
            'working_dir_prefix' : f'{transformer_to_str(transformer)}__switches.{switches:.2f}'
        }
        targets_new += [ target ]

print(f"[+] Switches-vs-Transformer: {len(targets_new)} targets")
TARGETS_BASE_DIR.joinpath(f'switches-vs-transformer.json').write_text(json.dumps(targets_new, indent=4))
