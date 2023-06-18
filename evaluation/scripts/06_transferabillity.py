
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from tqdm import tqdm
from itertools import repeat
from matplotlib.ticker import PercentFormatter

from config import *
from trial import Trial

import numpy as np
import json
import random

from collections import Counter

random.seed(2022)

trial_dir = DATA_DIR.joinpath(f'transferability')
trial = Trial(trial_dir, trial_dir.name)

data = []
for name, config in trial.config.items():
    if len(config["target"]["request"]) == 1 and len(config["target"]["reject"]) == 0:
        data += [name] 

subtrial = trial.data.loc[trial.data.name.isin(data)]

transferability = defaultdict(int)
for ix in range(100):
    no_success = 0
    for model_idx in range(8):
        if subtrial.iloc[ix][f'p_successful_{model_idx}'] != False:
            no_success += 1
    transferability[no_success] += 1


Y = []
for x in range(1, 9):
    successful = 0
    for ix in range(x, 9):
        successful += transferability[ix]
    Y += [ successful ]  
print(f"[+] Cumulative: {Y}")


idxes = {}
for idx in subtrial.index:
    success = np.sum([ subtrial.loc[idx][f'p_successful_{model_idx}'] is True for model_idx in range(8) ])
    skip = np.sum([ subtrial.loc[idx][f'p_successful_{model_idx}'] is None for model_idx in range(8) ])
    idxes[idx] = (success, skip)
sorter = list(zip(*sorted(idxes.items(), key=lambda x: x[1], reverse=True)))[0]

subtrial = subtrial.sort_values([f'p_successful_{idx}' for idx in reversed(range(0, 8))], ascending=[False]*8)

events = []
for idx in sorter:
    events += [[ subtrial.loc[idx][f'p_successful_{model_idx}'] for model_idx in range(8)]]

plot_data_pos = []
for model_idx in range(8):
    plot_data_pos += [[ event_idx for event_idx, event in enumerate(events) if event[model_idx] is True ]]

plot_data_net = []
for model_idx in range(8):
    plot_data_net += [[ event_idx for event_idx, event in enumerate(events) if event[model_idx] is None ]]

lineoffsets = [ idx for idx in range(8)]
linelengths = [ 0.8 ]*8

fig, ax = plt.subplots(figsize=(4.5, 2.5))

ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

ax.eventplot(plot_data_pos, lineoffsets=lineoffsets, linelengths=linelengths, color=colors['blue'])
ax.eventplot(plot_data_net, lineoffsets=lineoffsets, linelengths=linelengths, color=colors['blue']+'80')

ax.set_xlabel(f"Success of Adversarial Paper (yes/no)", fontsize="large")
ax.set_ylabel("Assignment System", fontsize="large")

ax.set_yticks(range(8))

fig.tight_layout()
plt.savefig(PLOTS_DIR.joinpath(f'transferability.pdf'))
plt.close()
print(f"[+] Saved plot @ {PLOTS_DIR.joinpath(f'transferability.pdf').relative_to(BASE_DIR)}")
