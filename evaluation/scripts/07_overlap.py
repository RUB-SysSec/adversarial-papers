import random
import re
from collections import defaultdict
from pathlib import Path

from utils.config import *
from utils.trial import Trial

random.seed(2022)

trial_dir = Path('/root/adversarial-papers/trials/overlap')
trial = Trial(trial_dir, trial_dir.name)

data = defaultdict(list)
for name, config in trial.config.items():
    overlap = re.findall(f'overlap_(\d.\d\d)__', name)[0]
    data[overlap] += [ name ]

print(f'[+] Overlap')
for overlap in ['0.00', '0.30', '0.70', '1.00']:
    subtrial = trial.data.loc[trial.data.name.isin(data[overlap])]
    print(f'    -> {overlap}: {subtrial.p_successful.sum() / (subtrial.p_successful.sum() + subtrial.p_failed.sum())*100:.1f}%')
