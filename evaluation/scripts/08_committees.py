import re
from collections import Counter, defaultdict
from itertools import chain, product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, PercentFormatter
from tqdm import tqdm

from config import *
from trial import Trial

no_targets = 100

data_successful = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
data_failed = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
data_l1 = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

trial_dir = DATA_DIR.joinpath('committees')
trial = Trial(trial_dir, trial_dir.name, only_featurespace=False)

f_successful = trial.data.set_index('name').to_dict()['f_successful']
f_failed = trial.data.set_index('name').to_dict()['f_failed']
f_l1 = trial.data.set_index('name').to_dict()['f_l1']

for name, config in trial.config.items():
    assert f_successful[name] == 1 - f_failed[name]
    reviewers, model_idx = re.findall(r'reviewers_(\d+)__.*__victim\.(\d+)__.*', name).pop()
    if len(config["target"]["request"]) == 1 and len(config["target"]["reject"]) == 0:
        data_l1['selection'][int(reviewers)][model_idx] += [f_l1[name]]
        data_successful['selection'][int(reviewers)][model_idx] += f_successful[name]
        data_failed['selection'][int(reviewers)][model_idx] += f_failed[name]

    if len(config["target"]["request"]) == 0 and len(config["target"]["reject"]) == 1:
        data_l1['rejection'][int(reviewers)][model_idx] += [f_l1[name]]
        data_successful['rejection'][int(reviewers)][model_idx] += f_successful[name]
        data_failed['rejection'][int(reviewers)][model_idx] += f_failed[name]

    if len(config["target"]["request"]) == 1 and len(config["target"]["reject"]) == 1:
        data_l1['substitution'][int(reviewers)][model_idx] += [f_l1[name]]
        data_successful['substitution'][int(reviewers)][model_idx] += f_successful[name]
        data_failed['substitution'][int(reviewers)][model_idx] += f_failed[name]

fig, ax = plt.subplots(figsize=(4.7,2.5))
ax.grid(alpha=.7)

ax.set_ylim([200, 4300])

ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.set_xlabel(f"Committee Size (\# Reviewers)", fontsize="large")
ax.set_ylabel("\# Modified Words ($L_1$)", fontsize="large")
ax.set_axisbelow(True)

colors_idxes = ['green', 'blue', 'orange']

for idx, (targets, marker) in enumerate([('selection', 'o'), ('rejection', '^'), ('substitution', 'v')]):
    X = []
    Y = []
    Y_std = []
    for no_reviewers in [100, 200, 300, 400, 500]:
        X += [no_reviewers]
        l1 = [ np.mean(l1_values) for model_idx, l1_values in data_l1[targets][no_reviewers].items() ]
        Y += [ np.mean(l1) ]
        Y_std += [ np.std(l1) ]

    ax.plot(X, Y, label=targets.capitalize(), color=colors[colors_idxes[idx]], marker=marker, markersize=2.5, markevery=1, linewidth=1, linestyle='solid')
    ax.fill_between(X, np.array(Y) - np.array(Y_std), np.array(Y) + np.array(Y_std), color=colors[colors_idxes[idx]], alpha=0.1)

ax.set_xticks(X)

fig.legend(loc='center',  fontsize='small', bbox_to_anchor=(0.57, 0.93), ncol=3)
fig.tight_layout()
plt.subplots_adjust(top=0.87)

plt.savefig(PLOTS_DIR.joinpath(f'committees.pdf'))
print(f"[+] Saved plot @ {PLOTS_DIR.joinpath(f'committees.pdf').relative_to(BASE_DIR)}")
plt.close()
