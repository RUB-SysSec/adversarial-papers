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

trial_dir = DATA_DIR.joinpath('generalization-of-attack')
usenix_trial = Trial(trial_dir, 'USENIX \'20', only_featurespace=False)

trial_dir = DATA_DIR.joinpath('featurespace-search')
sp_trial = Trial(trial_dir, 'IEEE S&P \'22', only_featurespace=False)

data_table = {}
for trial in [usenix_trial, sp_trial]:
    

    data_table[trial.label] = [
        f'{trial.data.loc[lambda df: df["p_successful"] == 1.0].running_time.count() / trial.data.running_time.count()*100:.2f}%',
        f'{format_running_time(trial.data.running_time.median())}',
        f'{trial.data.loc[lambda df: df["p_successful"] == 1.0].p_l1.median()}',
        f'{trial.data.loc[lambda df: df["p_successful"] == 1.0].p_linf.median()}'

    ]

df = pd.DataFrame(data_table, index=["Success Rate", "Running Time", "L1", "Linf"])
print(f"{df}")
