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

no_models = 8
no_targets = 1000 # all select combinations

targets_dir = TARGETS_BASE_DIR
oakland_submissions = SUBMISSIONS_BASE_DIR / "oakland_22" / "pdf_compiled"
usenix_submissions = SUBMISSIONS_BASE_DIR / "usenix_20" / "pdf_compiled"
oakland_submissions_srcs = SUBMISSIONS_BASE_DIR  / "oakland_22" / "arxiv-sources" / "submissions_latexpanded"
usenix_submissions_srcs = SUBMISSIONS_BASE_DIR  / "usenix_20" / "arxiv-sources" / "submissions_latexpanded"

submission_pdfs = [ submission_pdf 
                    for submission_pdf in chain(oakland_submissions.glob("*.pdf"), usenix_submissions.glob('*.pdf'))
                    if submission_pdf.stem not in ['1911.05673', '1908.02444'] ]
submission_srcs = { submission_src.name : submission_src 
                    for submission_src in chain(oakland_submissions_srcs.glob("*"), usenix_submissions_srcs.glob('*')) }

targets_all = []

for no_reviewers in [100, 200, 300, 400, 500]:
    print(f"\n[+] Reviewers {no_reviewers}")

    models = [ AutoBid(MODELS_BASE_DIR.joinpath('committees', f'{no_reviewers}', f'{model_idx:>02}')) 
            for model_idx in tqdm(range(no_models), ncols=80) ]

    for no_select, no_reject in [(1, 0)]:
        print(f'\n[+] Get targets (no select: {no_select}, no reject: {no_reject})')
        for model in models:
            targets = []
            for submission_pdf in tqdm(submission_pdfs, ncols=80):
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
                            'submission' : f'{submission_srcs[submission_pdf.stem].relative_to(SUBMISSIONS_BASE_DIR).as_posix()}',
                            'target_reviewer' : { 'request' : selected,
                                                'reject' : rejected},
                            'victim_models' : [ f'{model.model_dir.relative_to(MODELS_BASE_DIR).as_posix()}' ],
                            'surrogate_models' : [ f'{model.model_dir.relative_to(MODELS_BASE_DIR).as_posix()}' ],
                            'working_dir_prefix' : f'reviewers.{no_reviewers}'
                        }]
            # randomly pick `no_targets` targets
            random.seed(2022)
            k = min(len(targets), no_targets)
            targets = random.sample(targets, k)
            
            targets_all += targets

configs_all = []
for margin in [0, -0.1, -0.2]:
    configs = []
    for target in targets_all:
        configs += [{
            'submission' : target['submission'],
            'target_reviewer' : target['target_reviewer'],
            'victim_models' : target['victim_models'],
            'surrogate_models' : target['surrogate_models'],
            'featurespace_config' :  { 'delta' : margin },
            'working_dir_prefix' : f'{target["working_dir_prefix"]}__margin.{margin}'
        }]
    configs_all += configs

targets_file = targets_dir.joinpath(f'load_balancing.json')
targets_file.write_text(json.dumps(configs_all, indent=4))
