import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import sys
from pathlib import Path
sys.path.append(Path.home().joinpath('adversarial-papers', 'src').as_posix())  
sys.path.append(Path.home().joinpath('adversarial-papers', 'plots').as_posix())  
import json
import shutil
from collections import defaultdict
from itertools import chain, combinations
import random
import numpy as np
from autobid import AutoBid
from problemspace.PdfLatexSource import PdfLatexSource
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

CORPUS_DIR = Path.home() / 'adversarial-papers' / 'evaluation' / 'corpus' / 'oakland_22_large'
MODELS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'models')
MORPHING_DIR = Path().home() / 'adversarial-papers' / 'scripts' / 'morphing'

models_dir = MODELS_BASE_DIR / "victim"
no_models = 8

print(f'[+] Load models')
models = [ AutoBid(models_dir.joinpath(f'{model_idx:>02}')) for model_idx in tqdm(range(no_models), ncols=80) ]

reviewers = models[0].reviewers_list

print(f'\n[+] Loads PDF files')
with Pool(cpu_count()) as p:
    pdf_files = list(set(CORPUS_DIR.rglob('*.pdf')))
    corpus = { pdf_file.name : words for words, pdf_file in tqdm(zip(p.imap(AutoBid.parse_pdf_file, pdf_files, chunksize=1), pdf_files), total=len(pdf_files), ncols=80) }

reviewer_to_paper = defaultdict(lambda: defaultdict(list))
for model in models:
    model_idx = model.model_dir.relative_to(MODELS_BASE_DIR).as_posix()
    print(f'\n{model_idx.upper()}')
    for paper, words in tqdm(corpus.items(), ncols=80):
        for reviewer, _ in model.get_ranking(words)[:5]:
            reviewer_to_paper[model_idx][reviewer] += [paper]
MORPHING_DIR.joinpath('reviewer_to_paper.json').write_text(json.dumps(reviewer_to_paper, indent=4))
