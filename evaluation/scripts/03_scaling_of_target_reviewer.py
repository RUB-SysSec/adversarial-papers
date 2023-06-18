
import random
from collections import defaultdict
from itertools import chain, product
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import seaborn as sns

from config import *
from trial import Trial

# color map
cmap = sns.diverging_palette(220, 20, l=40, s=80, as_cmap=True)

trials_dir = [ DATA_DIR.joinpath('scaling-of-targets') ]

data = defaultdict(list)
for trial_dir in trials_dir:
    trial = Trial(trial_dir, trial_dir.name, only_featurespace=False)

    p_l1 = trial.data[["name", "p_l1"]].set_index("name").to_dict()['p_l1']
    p_successful = trial.data[["name", "p_successful"]].set_index("name").to_dict()['p_successful']
    for name, config in trial.config.items():

        no_request = len(config["target"]["request"])
        no_reject = len(config["target"]["reject"])

        data[(no_reject, no_request)] += [ (p_l1[name], p_successful[name] == 1) ]

for k, v in data.items():
    words, success = zip(*v)
    data[k] = np.median(words), np.sum(success) / 100

# create heatmap matrix
no_requested =  [ 0,  1,  2,  3,  4,  5 ]
no_rejected =   [ 0,  1,  2 ]
words = np.zeros((3,6))
for no_request, no_reject in product(no_requested, no_rejected):
    if no_request == 0 and no_reject == 0:
        words[0][0] = 0
        continue 
    no_request_idx = no_requested.index(no_request) 
    no_reject_idx = no_rejected.index(no_reject)
    try:
        words[no_reject_idx][no_request_idx] = data[(no_reject, no_request)][0]
    except:
        words[no_reject_idx][no_request_idx] = 0

# plot
fig, ax = plt.subplots(figsize=(4.5, 2.8))
im = ax.imshow(words, cmap=cmap, vmin=-500, vmax=5000)

# add text to tiles 
for i, j in product(range(len(no_rejected)), range(len(no_requested))):
    if words[i, j] == 0:
        ax.text(j, i, f'$L_1$', ha="center", va="bottom", color="black")
        ax.text(j, i+0.07, f'Success\nRate', ha="center", va="top", color="black", fontsize=8)
        continue
    ax.text(j, i, f'\n {data[(i, j)][1]*100:5.2f}\%', ha="center", va="top", color="black", fontsize=8)
    ax.text(j, i, f'{data[(i, j)][0]:>4.0f}', ha="center", va="bottom", color="black")

# formatting
ax.set_xticks(np.arange(len(no_requested)))
ax.set_yticks(np.arange(len(no_rejected)))
ax.set_xticklabels([str(no_request) for no_request in no_requested])
ax.set_yticklabels([str(no_reject) for no_reject in no_rejected])

ax.set_ylabel("\# Rejected Reviewer", fontsize="large")
ax.set_xlabel("\# Selected Reviewer", fontsize="large")

fig.tight_layout()
fig.savefig(PLOTS_DIR.joinpath(f'scaling-of-targets.pdf').relative_to(BASE_DIR))
print(f"[+] Saved plot @ {PLOTS_DIR.joinpath(f'scaling-of-targets.pdf').relative_to(BASE_DIR)}")