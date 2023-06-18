import json
import random

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter

from config import *
from trial import Trial

random.seed(2022)

reviewer_load = 10
data = json.loads(DATA_DIR.joinpath('load_balancing.json').read_text())

fig, ax = plt.subplots(figsize=(4.7,2.5))
ax.grid(alpha=.7)

ax.yaxis.set_major_formatter(PercentFormatter(1.0))
ax.set_ylim([0.4, 0.9])

ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.set_xlabel(f"\# Submissions", fontsize="large")
ax.set_ylabel("Success Rate", fontsize="large")
ax.set_axisbelow(True)

data_points = 0
for idx, margin in enumerate(["0.0", "-0.1", "-0.2"]):
    X = []
    Y = []
    Y_std = []
    for no_reviewer in ["100", "200", "300", "400", "500"]:
        success_rates = []
        for model_idx in ["00", "01", "02", "03", "04", "05", "06", "07"]:
            try:
                success_rates += [ data[no_reviewer][margin][model_idx]['success'] / ( data[no_reviewer][margin][model_idx]['failed'] + data[no_reviewer][margin][model_idx]['success']) ]
                data_points += data[no_reviewer][margin][model_idx]['success'] + data[no_reviewer][margin][model_idx]['failed'] + data[no_reviewer][margin][model_idx]['invalid']  
            except KeyError:
                pass
        X += [(int(no_reviewer)*reviewer_load)//5]
        Y += [np.mean(success_rates)]
        Y_std += [np.std(success_rates)]
    ax.plot(X, Y, label=f'Margin {abs(float(margin)):4.2f}', color=colors[colors_idxes[idx]], marker='o', markersize=2.5, markevery=1, linewidth=1, linestyle='solid')
    ax.fill_between(X, np.array(Y) - np.array(Y_std), np.array(Y) + np.array(Y_std), color=colors[colors_idxes[idx]], alpha=0.1)

ax.set_xticks(X)

fig.legend(loc='center',  fontsize='small', bbox_to_anchor=(0.57, 0.93), ncol=3)
fig.tight_layout()
plt.subplots_adjust(top=0.87)
plt.savefig(PLOTS_DIR.joinpath(f'load_balancing.pdf'))
plt.close()
print(f"[+] Saved plot @ {PLOTS_DIR.joinpath(f'load_balancing.pdf').relative_to(BASE_DIR)}")
