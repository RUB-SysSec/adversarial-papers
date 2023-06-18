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

trial_dir = DATA_DIR.joinpath('featurespace-search')
trial = Trial(trial_dir, trial_dir.name, only_featurespace=False)

# sort data into objectives
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

# stats
print(f"Feature-Space Search".upper())
print(f'[+] Overall success rate')
print(f'    -> {trial.data.loc[lambda df: df["p_successful"] == 1.0].running_time.count() / trial.data.running_time.count()*100:.2f}%')

print(f'\n[+] Overall run-time')
print(f'    -> median: {format_running_time(trial.data.running_time.median())}')

print(f'\n[+] Overall L1')
print(f'    -> min   : {trial.data.loc[lambda df: df["p_successful"] == 1.0].p_l1.min()}')
print(f'    -> max   : {trial.data.loc[lambda df: df["p_successful"] == 1.0].p_l1.max()}')

print(f'\n[+] Ratio between modifications and original content')
subtrial = trial.data.loc[trial.data.name.isin([ r for ix in range(8) for r in data[ix]['selection']])]
print(f'    -> selection: {subtrial.loc[lambda df: df["p_successful"] == 1.0].p_l1_frac.median()*100:.2f}%')
subtrial = trial.data.loc[trial.data.name.isin([ r for ix in range(8) for r in data[ix]['rejection']])]
print(f'    -> rejection: {subtrial.loc[lambda df: df["p_successful"] == 1.0].p_l1_frac.median()*100:.2f}%')


print(f'\n[+] Modifications per objective')
data_table = {}
for targets in ['selection', 'rejection', 'substitution']:

    data_per_model = defaultdict(list)
    for model_idx in range(len(data)):
        data_from_model = trial.data.loc[trial.data.name.isin(data[model_idx][targets])]
        data_per_model['p_l1'] += [ data_from_model.p_l1.median() ]
        data_per_model['p_linf'] += [ data_from_model.p_linf.median() ]

    data_table[targets.capitalize()] = [
        f"{np.average(data_per_model['p_l1']):.0f}",
        f"{np.average(data_per_model['p_linf']):.0f}",
     ]

df = pd.DataFrame(data_table, index=["    L1", "    Linf"])
print(f"{df}")