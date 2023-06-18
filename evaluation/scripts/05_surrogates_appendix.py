import re
from collections import defaultdict
from itertools import product, repeat
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.ticker import PercentFormatter
from tqdm import tqdm

from config import *
from trial import Trial

NO_SURROGATES = sorted([ int(d.name.split('-')[1]) for d in DATA_DIR.glob(f'surrogates-*')])

color_gray = colors['grey']
color_median = '#EEEEEEEE'
colors = [ colors['orange']+'D0',colors['blue']+'D0', colors['green']+'D0']

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
            results[targets][no_surrogates] += list(subset.p_l1)

data = defaultdict(list)
for targets, no_surrogates in product(['selection', 'rejection', 'substitution'], NO_SURROGATES):
    data[targets] += [ results[targets][no_surrogates] ]

# plot
fig, axs = plt.subplots(nrows=3, ncols=1, sharex=True, figsize=(4.5,5))

for targets, color, ax in zip(['selection', 'rejection', 'substitution'], colors, axs):

    print(f'\n[+] Median L1 norm {targets[0].upper()}{targets[1:]}')
    for no_surrogates, d in zip(NO_SURROGATES, data[targets]):
        print(f'    {no_surrogates}: {np.median(d):.0f}')

    # boxplot
    bp = ax.boxplot(list(reversed(data[targets])), patch_artist=True, vert=0,  whis=1.5, widths=0.5, showfliers=True)
    # style of outliers
    for flier in bp['fliers']:
        flier.set(marker ='x',
                color='#9e2a2b',
                alpha=0.5) 
    # style of medians
    for median in bp['medians']:
        median.set(color=color_median, linewidth=1)
    # style of boxes
    for box in bp['boxes']:
        box.set_color(color_gray)
        box.set_facecolor(color)
    # formatting
    ax.set_title(targets.capitalize(), fontsize="large")
    ax.grid(alpha=.7)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(ticker.FixedFormatter(list(reversed(NO_SURROGATES))))
    if targets == 'rejection':
        ax.set_ylabel("Ensemble Size", fontsize="large")

ax.set_xlabel("\#Modified Words ($L_1$)", fontsize="large")

fig.tight_layout()
fig.savefig(PLOTS_DIR.joinpath(f'surrogates_appendix.pdf'))
print(f"\n[+] Saved plot @ {PLOTS_DIR.joinpath(f'surrogates_appendix.pdf').relative_to(BASE_DIR)}")