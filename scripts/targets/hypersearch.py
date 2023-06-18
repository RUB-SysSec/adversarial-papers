import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
from pathlib import Path
import sys
sys.path.append(Path.home().joinpath('adversarial-papers', 'src').as_posix())  

import json
import shutil
from collections import defaultdict
from itertools import chain, combinations
import random
import numpy as np
from autobid import AutoBid
from problemspace.PdfLatexSource import PdfLatexSource
from tqdm import tqdm

SUBMISSIONS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'submissions')
MODELS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'models')
TARGETS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'targets')

models_dir = MODELS_BASE_DIR / "hypersearch" / 'victim'
surrogate_models_dir = MODELS_BASE_DIR / "hypersearch" / 'overlap_0.70'
targets_dir = TARGETS_BASE_DIR / "hypersearch"
submissions_dir_sources = SUBMISSIONS_BASE_DIR  / "oakland_22" / "arxiv-sources" / "submissions_latexpanded"
submissions_dir_compiled = SUBMISSIONS_BASE_DIR / "oakland_22" / "pdf_compiled"

no_models = 8
no_targets = 100 

random.seed(2022)

# compile PDFs
if not submissions_dir_compiled.is_dir():
    submissions_dir_compiled.mkdir()
    for submission_dir_source in submissions_dir_sources.glob('*'):
        try:
            _, submission_pdf = PdfLatexSource.get_pdf_from_source(submission_dir_source, 'main.tex')
            shutil.copyfile(submission_pdf, submissions_dir_compiled.joinpath(f'{submission_dir_source.name}.pdf'))
            print(submission_dir_source.name)
        except Exception as e:
            # skip submission if compilation fails
            print(f"[!] Error {submission_dir_source.name}")
            continue

print("[+] Load models")
models = [ AutoBid(models_dir.joinpath(f'{model_idx:>02}')) for model_idx in tqdm(range(no_models), ncols=80) ]

targets = []
for no_select, no_reject in [(1, 0), (0, 1), (1, 1)]:
    print(f'\n[+] Get targets (no select: {no_select}, no reject: {no_reject})')
    for model in tqdm(models, ncols=80):
        
        targets_model = []
        for submission_pdf in sorted(submissions_dir_compiled.glob('*.pdf')):

            # get initial ranking
            ranking = model.get_ranking(submission_pdf)
            top_10 = [ name for name, _ in ranking[:10]]

            # select targets
            for target_reviewer in list(combinations(top_10, no_reject + no_select)):
                for selected in combinations(target_reviewer, no_select):
                    rejected = [ r for r in target_reviewer if r not in selected ]
                    # exclude targets that can be solved trivially
                    if  (len(selected) > 0 and set(selected).issubset(set(top_10[:5]))) or \
                        (len(rejected) > 0 and set(rejected).issubset(set(top_10[5:]))):
                        continue
                    # add target
                    targets_model += [{
                        'submission' : f'{submissions_dir_sources.joinpath(submission_pdf.stem).relative_to(SUBMISSIONS_BASE_DIR).as_posix()}',
                        'target_reviewer' : { 'request' : selected,
                                              'reject' : rejected},
                        'victim_models' : [ f'{model.model_dir.relative_to(MODELS_BASE_DIR).as_posix()}' ],
                        'surrogate_models' : [ f'{model.model_dir.relative_to(MODELS_BASE_DIR).as_posix()}' ]
                    }]

        # randomly pick `no_targets` targets per combination
        random.seed(2022)
        k = min(len(targets_model), no_targets)
        targets += list(random.sample(targets_model, k))

print(f'\n[+] Select {no_targets} from {len(targets)} targets')

# randomly pick `no_targets` targets
random.seed(2022)
k = min(len(targets), no_targets)
targets = random.sample(targets, k)

# save targets
targets_file = targets_dir.joinpath(f'whitebox.json')
targets_file.parent.mkdir(exist_ok=True)
targets_file.write_text(json.dumps(targets, indent=4))

# blackbox
surrogate_models = [ surrogate_models_dir.joinpath(f'{model_idx:>02}') for model_idx in range(8) ]

configs = []
for target in targets:
    surrogate_models = random.sample(surrogate_models, k=1)
    configs += [{
        'submission' : target['submission'],
        'target_reviewer' : target['target_reviewer'],
        'victim_models' : target['victim_models'],
        'surrogate_models' : [ f'{model_dir.relative_to(MODELS_BASE_DIR).as_posix()}' for model_dir in surrogate_models ]
    }]

targets_dir.joinpath(f'blackbox.json').write_text(json.dumps(configs, indent=4))
