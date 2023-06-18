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

BASE_DIR = Path.home().joinpath('adversarial-papers')

SUBMISSIONS_BASE_DIR = BASE_DIR.joinpath('evaluation', 'submissions')
MODELS_BASE_DIR = BASE_DIR.joinpath('evaluation', 'models')
TARGETS_BASE_DIR = BASE_DIR.joinpath('evaluation', 'targets')

models_dir = MODELS_BASE_DIR / "victim"
targets_dir = TARGETS_BASE_DIR
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

targets_full = []
targets_selection = []

print('[+] Select targets')
for model in tqdm(models, ncols=80):
    for no_select, no_reject in [(1, 0), (0, 1), (1, 1)]:
        targets = []
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
                    targets += [{
                        'submission' : f'{submissions_dir_sources.joinpath(submission_pdf.stem).relative_to(SUBMISSIONS_BASE_DIR).as_posix()}',
                        'target_reviewer' : { 'request' : selected,
                                                'reject' : rejected},
                        'victim_models' : [ f'{model.model_dir.relative_to(MODELS_BASE_DIR).as_posix()}' ],
                        'surrogate_models' : [ f'{model.model_dir.relative_to(MODELS_BASE_DIR).as_posix()}' ]
                    }]

        # randomly pick `no_targets` targets
        random.seed(2022)
        k = min(len(targets), no_targets)
        targets = random.sample(targets, k)

        # save targets
        targets_full += targets
        if no_select == 1 and no_reject == 0:
            targets_selection += targets

# save targets
targets_file = targets_dir.joinpath(f'featurespace-search.json')
targets_file.write_text(json.dumps(targets_full, indent=4))

targets_file = targets_dir.joinpath(f'featurespace-search-selection.json')
targets_file.write_text(json.dumps(targets_selection, indent=4))