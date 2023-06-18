import re
from collections import defaultdict
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter
from tqdm import tqdm

from config import *
from trial import Trial

NO_SURROGATES = sorted([ int(d.name.split('-')[1]) for d in DATA_DIR.glob(f'surrogates-*')])
colors_idxes = ['green', 'blue', 'orange']

print(f'[+] Load trials')
results = defaultdict(lambda: defaultdict(list))
for no_surrogates in tqdm(NO_SURROGATES, ncols=80):
    trial_dir = DATA_DIR.joinpath(f'surrogates-{no_surrogates}')
    trial = Trial(trial_dir, trial_dir.name, only_featurespace=False)

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
    
    for targets in ['selection', 'rejection', 'substitution']:
        for victim_idx in range(8):
            subset = trial.data.loc[trial.data.name.isin(data[victim_idx][targets])]
            success = subset.loc[lambda df: df[f"p_successful_0"] == True][f'p_successful_0'].count()
            failed = subset.loc[lambda df: df[f"p_successful_0"] == False][f'p_successful_0'].count()
            finished = subset.running_time.count()
            success_rate = success / (success + failed) if finished > 0 else 0
            results[targets][no_surrogates] += [ (success_rate, finished) ]

fig, ax = plt.subplots(figsize=(4.5,2.5))
ax.grid(alpha=.7)

ax.yaxis.set_major_formatter(PercentFormatter(1.0))
ax.set_ylim([0, 1])

ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.set_xlabel(f"Ensemble Size", fontsize="large")
ax.set_ylabel("Success Rate", fontsize="large")
ax.set_axisbelow(True)

for idx, targets in enumerate(results):
    X = [1, 2, 3, 4, 5, 6, 7, 8]
    Y = [0]*8
    Y_std = [0]*8
    for (param_value, success_rates) in sorted(results[targets].items(), key=lambda x: x[0]):
        success_rates = [ success_rate[0] for success_rate in success_rates if success_rate[0] > 0 ]
        X[param_value-1] = param_value
        Y[param_value-1] = np.mean(success_rates)
        Y_std[param_value-1] = np.std(success_rates)
    ax.plot(X, Y, label=targets.capitalize(), color=colors[colors_idxes[idx]], marker='v', markersize=2.5, markevery=1, linewidth=1, linestyle='solid')
    ax.fill_between(X, np.array(Y) - np.array(Y_std), np.array(Y) + np.array(Y_std), color=colors[colors_idxes[idx]], alpha=0.1)

ax.set_xticks(X)

plt.legend(loc='lower right', fontsize='small')
fig.tight_layout()
plt.savefig(PLOTS_DIR.joinpath(f'surrogates.pdf'))
plt.close()
print(f"\n[+] Saved plot @ {PLOTS_DIR.joinpath(f'surrogates.pdf').relative_to(BASE_DIR)}")