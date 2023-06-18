from collections import defaultdict
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from config import *
from trial import Trial

color = [ colors['orange']+'D0',colors['blue']+'D0', colors['green']+'D0'][0]
targets = ["Selection", 'Rejection', 'Substitution'][0]

trial_dir = DATA_DIR.joinpath('featurespace-search')
trial = Trial(trial_dir, trial_dir.name, only_featurespace=False)

# sort data
p_l1 = trial.data[["name", "p_l1"]].set_index("name").to_dict()['p_l1']
data = defaultdict(lambda: defaultdict(list))
for name, config in trial.config.items():
    victim_model = int(Path(config['victim_model_dirs'][0]).stem)
    # selection
    if len(config["target"]["request"]) == 1 and len(config["target"]["reject"]) == 0:
        data[victim_model]["selection"] += [p_l1[name]] 
    # rejection
    if len(config["target"]["request"]) == 0 and len(config["target"]["reject"]) == 1:
        data[victim_model]["rejection"] += [p_l1[name]] 
    # substitution
    if len(config["target"]["request"]) == 1 and len(config["target"]["reject"]) == 1:
        data[victim_model]["substitution"] += [p_l1[name]] 

# plot
fig, ax = plt.subplots(figsize=(4.5,3))
# data
data_victim = [ data[victim_model][targets.lower()] for victim_model in range(8) ]
# boxplot
bp = ax.boxplot(list(reversed(data_victim)), patch_artist=True, vert=0,  whis=1.5, widths=0.5, showfliers=True)
# style of outliers
for flier in bp['fliers']:
    flier.set(marker ='x',
            color='#9e2a2b',
            alpha=0.5) 
# style of medians
for median in bp['medians']:
    median.set(color=colors['lightgrey'], linewidth=1)
# style of boxes
for box in bp['boxes']:
    box.set_color(colors['grey'])
    box.set_facecolor(color)
# formatting
ax.set_title(targets, fontsize="large")
ax.grid(alpha=.7)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.set_axisbelow(True)
ax.yaxis.set_major_formatter(ticker.FixedFormatter(list(reversed(range(8)))))
ax.set_ylabel("Assignment System", fontsize="large")

ax.set_xlabel("\#Modified Words ($L_1$)", fontsize="large")

fig.tight_layout()
fig.savefig(PLOTS_DIR.joinpath(f'featurespace_search.pdf'))
print(f"[+] Saved plot @ {PLOTS_DIR.joinpath(f'featurespace_search.pdf').relative_to(BASE_DIR)}")