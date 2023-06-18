from tqdm import tqdm
from pathlib import Path
import json
from math import log2
import numpy as np
from itertools import product, chain
import random
from collections import defaultdict

from config import *
from trial import Trial

overlap_cp = json.loads(DATA_DIR.joinpath('overlap_cross_entropy.json').read_text())
reviewers = list(overlap_cp['0.00'].keys())
print(f'[+] Overlap')
for idx, reviewer in enumerate(reviewers):
    print(f'    {idx+1:<2}', end='\t')
    for overlap in ['0.00', '0.30', '0.70', '1.00']:
        print(f'{np.mean(overlap_cp[overlap][reviewer]):4.2f}+-{np.std(overlap_cp[overlap][reviewer]):4.2f}', end='\t')
    print()
