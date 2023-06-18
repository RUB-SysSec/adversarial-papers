import json
from collections import defaultdict
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import numpy as np

from config import *
from trial import Trial

import warnings
warnings.filterwarnings("ignore")

trial_dir = DATA_DIR.joinpath('topic_baseline')
topic_trial = Trial(trial_dir, trial_dir.name, only_featurespace=False)

trial_dir = DATA_DIR.joinpath('morphing_baseline')
morphing_trial = Trial(trial_dir, trial_dir.name, only_featurespace=False)

for trial in [topic_trial, morphing_trial]:
    
    print(f'\n{trial.label.upper()}')
    print(f'[+] Success rate: { trial.data.loc[lambda df: df["p_successful"] == 1.0].running_time.count() / trial.data.running_time.count()*100:.2f}')
    print(f'[+] L1 (max)    : { trial.data.loc[lambda df: df["p_successful"] == 1.0].p_l1.max()}')

    # sort data
    p_l1 = trial.data[["name", "p_l1"]].set_index("name").to_dict()['p_l1']
    data = defaultdict(lambda: defaultdict(list))
    for name, config in trial.config.items():
        victim_model = int(Path(config['victim_model_dirs'][0]).stem)
        # selection
        if len(config["target"]["request"]) == 1 and len(config["target"]["reject"]) == 0:
            data[victim_model]["selection"] += [name] 
        # rejection
        if len(config["target"]["request"]) == 0 and len(config["target"]["reject"]) == 1:
            data[victim_model]["rejection"] += [name] 
        # substitution
        if len(config["target"]["request"]) == 1 and len(config["target"]["reject"]) == 1:
            data[victim_model]["substitution"] += [name] 

    print(f'[+] Table')
    data_table = {}
    for targets in ['selection', 'rejection', 'substitution']:

        data_per_model = defaultdict(list)
        for model_idx in range(len(data)):
            data_from_model = trial.data.loc[trial.data.name.isin(data[model_idx][targets])]
            data_per_model['p_l1'] += [ data_from_model.p_l1.median() ]
            data_per_model['p_linf'] += [ data_from_model.p_linf.median() ]
            data_per_model['running_time'] += [ data_from_model.running_time.median() ] 
            data_per_model['targets'] += [ data_from_model.running_time.count() ]

        success_rate = np.sum(data_per_model['success_rate']) / np.sum(data_per_model['targets']) * 100
        l1 = np.average(data_per_model['p_l1'])
        linf = np.average(data_per_model['p_linf'])
        data_table[targets.capitalize()] = [
            f"{l1:.0f}",
            f"{linf:.0f}",
        ]

    df = pd.DataFrame(data_table, index=["L1", "Linf"])
    print(f"{df}")
