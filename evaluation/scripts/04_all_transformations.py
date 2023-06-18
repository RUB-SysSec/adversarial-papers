import re
from collections import Counter, defaultdict
from itertools import product, chain
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter, FixedLocator
from tqdm import tqdm


from config import *
from trial import Trial

no_targets = 100

#
# BUDGET vs TRANSFORMER
#

budget_trial_dirs = list(DATA_DIR.glob('budget-vs-transformer*'))

data_budget = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
budgets, transformers = [], []
for trial_idx, trial_dir in enumerate(budget_trial_dirs):
    trial = Trial(trial_dir, trial_dir.name, only_featurespace=False)
    p_successful = trial.data.set_index('name').to_dict()['p_successful']
    p_failed = trial.data.set_index('name').to_dict()['p_failed']

    for name, config in trial.config.items():
        assert p_successful[name] == 1 - p_failed[name]
        transformer, budget = re.findall(r'(.+)__budget\.(\d+.\d+)__.*', name).pop()
        data_budget[float(budget)][transformer][trial_idx] += p_successful[name]
        budgets += [float(budget)]
        transformers += [transformer]

std_budget = defaultdict(lambda: defaultdict(float))
for budget, transformer in product(set(budgets), set(transformers)):
    std_budget[float(budget)][transformer] = np.std(list(data_budget[float(budget)][transformer].values()))
    data_budget[float(budget)][transformer] = np.mean(list(data_budget[float(budget)][transformer].values()))

#
# SWITCHES vs TRANSFORMER
#

switches_trial_dirs = list(DATA_DIR.glob('switches-vs-transformer*'))

data_switches = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
switchess, transformers = [], []

for trial_idx, trial_dir in enumerate(switches_trial_dirs):
    trial = Trial(trial_dir, trial_dir.name, only_featurespace=False)

    p_successful = trial.data.set_index('name').to_dict()['p_successful']
    p_failed = trial.data.set_index('name').to_dict()['p_failed']

    for name, config in trial.config.items():
        assert p_successful[name] == 1 - p_failed[name]
        transformer, budget = re.findall(r'(.+)__switches\.(\d+\.\d+)__.*', name).pop()
        data_switches[int(float(budget))][transformer][trial_idx] += p_successful[name]
        switchess += [float(budget)]
        transformers += [transformer]

std_switches = defaultdict(lambda: defaultdict(float))
for switches, transformer in product(set(switchess), set(transformers)):
    std_switches[float(switches)][transformer] = np.std(list(data_switches[float(switches)][transformer].values()))
    data_switches[float(switches)][transformer] = np.mean(list(data_switches[float(switches)][transformer].values()))


# PLOT
fig, axs = plt.subplots(nrows=1, ncols=2, sharey=True, figsize=(4.5, 2.7))

# SWITCHES
Y = [1, 2, 4, 8, 16]

X_text = np.array([ data_switches[y]['text'] for y in Y ])
X_text_encoding = np.array([ data_switches[y]['text-encoding'] for y in Y ])
X_text_encoding_format = np.array([ data_switches[y]['text-encoding-format'] for y in Y ])

X_std_text = np.array([ std_switches[y]['text'] for y in Y ])
X_std_text_encoding = np.array([ std_switches[y]['text-encoding'] for y in Y ])
X_std_text_encoding_format = np.array([ std_switches[y]['text-encoding-format'] for y in Y ])


print('[+] Switches')
if len(switches_trial_dirs) == 0:
    print(f'    found no trials')

else:
    print("                ", " ".join([f'{x:6.2f}' for x in Y]))
    print("    Text      : ", " ".join([f'{x:6.2f}' for x in X_text]))
    print("    + Encoding: ", " ".join([f'{x:6.2f}' for x in X_text_encoding]))
    print("    + Format  : ", " ".join([f'{x:6.2f}' for x in X_text_encoding_format]))

    axs[1].bar(range(len(Y)), X_text, 0.7, color=colors['blue']+'E8')
    axs[1].bar(range(len(Y)), np.amax(np.array([X_text_encoding-X_text, np.zeros(len(X_text))]), axis=0), 0.7, bottom=X_text, color=colors['orange']+'E8')
    axs[1].bar(range(len(Y)), X_text_encoding_format-np.amax(np.array([X_text_encoding, X_text]), axis=0), 0.7, bottom=np.amax(np.array([X_text_encoding, X_text]), axis=0), color=colors['green']+'E8')

    axs[1].bar([a-0.1 for a in range(len(Y))], X_text, 0.7, yerr=X_std_text, ecolor=colors['darkblue'], color=colors['blue']+'00')
    axs[1].bar([a+0.1 for a in range(len(Y))], np.amax(np.array([X_text_encoding-X_text, np.zeros(len(X_text))]), axis=0), 0.7, ecolor=colors['darkorange'], yerr=X_std_text_encoding, bottom=X_text, color=colors['orange']+'00')
    axs[1].bar([a for a in range(len(Y))], X_text_encoding_format-np.amax(np.array([X_text_encoding, X_text]), axis=0), 0.7, ecolor=colors['darkgreen'], yerr=X_std_text_encoding_format, bottom=np.amax(np.array([X_text_encoding, X_text]), axis=0), color=colors['green']+'00')

axs[1].set_axisbelow(True)
axs[1].grid(alpha=.7)
axs[1].spines['right'].set_visible(False)
axs[1].spines['top'].set_visible(False)

axs[1].yaxis.set_major_formatter(PercentFormatter(no_targets))

axs[1].set_xlabel("\# Switches ($S$)", fontsize="large")

axs[1].xaxis.set_major_locator(FixedLocator(range(len(Y))))
axs[1].xaxis.set_ticklabels(Y)

## BUDGET

Y = [0.25, 0.5, 1, 2, 4]

X_text = np.array([ data_budget[y]['text'] for y in Y ])
X_text_encoding = np.array([ data_budget[y]['text-encoding'] for y in Y ])
X_text_encoding_format = np.array([ data_budget[y]['text-encoding-format'] for y in Y ])

X_std_text = np.array([ std_budget[y]['text'] for y in Y ])
X_std_text_encoding = np.array([ std_budget[y]['text-encoding'] for y in Y ])
X_std_text_encoding_format = np.array([ std_budget[y]['text-encoding-format'] for y in Y ])

print('\n[+] Budget')
if len(budget_trial_dirs) == 0:
    print(f'    found no trials')

else:
    print("                ", " ".join([f'{x:6.2f}' for x in Y]))
    print("    Text      : ", " ".join([f'{x:6.2f}' for x in X_text]))
    print("    + Encoding: ", " ".join([f'{x:6.2f}' for x in X_text_encoding]))
    print("    + Format  : ", " ".join([f'{x:6.2f}' for x in X_text_encoding_format]))

    axs[0].bar(range(len(Y)), X_text, 0.7, color=colors['blue']+'E8')
    axs[0].bar(range(len(Y)), np.amax(np.array([X_text_encoding-X_text, np.zeros(len(X_text))]), axis=0), 0.7, bottom=X_text, color=colors['orange']+'E8')
    axs[0].bar(range(len(Y)), X_text_encoding_format-np.amax(np.array([X_text_encoding, X_text]), axis=0), 0.7, bottom=np.amax(np.array([X_text_encoding, X_text]), axis=0), color=colors['green']+'E8')

    axs[0].bar([a-0.1 for a in range(len(Y))], X_text, 0.5, ecolor=colors['darkblue'], yerr=X_std_text, color=colors['blue']+'00')
    axs[0].bar([a+0.1 for a in range(len(Y))], np.amax(np.array([X_text_encoding-X_text, np.zeros(len(X_text))]), axis=0), 0.7, ecolor=colors['darkorange'], yerr=X_std_text_encoding, bottom=X_text, color=colors['orange']+'00')
    axs[0].bar([a+0 for a in range(len(Y))], X_text_encoding_format-np.amax(np.array([X_text_encoding, X_text]), axis=0), 0.7, ecolor=colors['darkgreen'], yerr=X_std_text_encoding_format, bottom=np.amax(np.array([X_text_encoding, X_text]), axis=0), color=colors['green']+'00')

axs[0].set_axisbelow(True)
axs[0].grid(alpha=.7)
axs[0].spines['right'].set_visible(False)
axs[0].spines['top'].set_visible(False)

axs[0].yaxis.set_major_formatter(PercentFormatter(no_targets))

axs[0].set_xlabel("Attack Budget ($\sigma$)", fontsize="large")

axs[0].xaxis.set_major_locator(FixedLocator(range(len(Y))))
axs[0].xaxis.set_ticklabels(Y)

# GENERAL
axs[0].set_ylabel(f"Success Rate", fontsize="large")
fig.legend(loc='center', labels=['Text', '+ Encoding', '+ Format'],
           bbox_to_anchor=(0.57, 0.93), ncol=3)
fig.tight_layout()
plt.subplots_adjust(top=0.87)

plt.savefig(PLOTS_DIR.joinpath(f'all-transformations.pdf'))
plt.close()
print(f"\n[+] Saved plot @ {PLOTS_DIR.joinpath(f'all-transformations.pdf').relative_to(BASE_DIR)}")