from pathlib import Path
import sys
sys.path.append(Path.home().joinpath('adversarial-papers', 'src').as_posix())  

import json
import shutil
from collections import defaultdict

import numpy as np
from autobid import AutoBid
from problemspace.PdfLatexSource import PdfLatexSource
from tqdm import tqdm, trange

model_dirs = Path.home() / "adversarial-papers" / "evaluation" / "models" / "victim"
submissions_dir_sources =  Path.home() / "adversarial-papers" / "evaluation" / "submissions" / "oakland_22" / "arxiv-sources" / "submissions_latexpanded"
submissions_dir_compiled =  Path.home() / "adversarial-papers" / "evaluation" / "submissions" / "oakland_22" / "pdf_compiled"
submissions_dir_ranking = Path.home() / "adversarial-papers" / "evaluation" / "submissions" / "oakland_22" / "victim_ranking"

if submissions_dir_ranking.is_dir():
    print(f"[+] Median ranking already exists @ {submissions_dir_ranking}")
    exit()
submissions_dir_ranking.mkdir()

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

# get rankings
print("[+] Load models")
models = [ AutoBid(model_dirs.joinpath(f'{model_idx:>02}')) for model_idx in trange(8, ncols=80) ]
reviewers = models[0].reviewers_list

for submission in submissions_dir_compiled.glob('*.pdf'):
    print(f'\n[+] {submission.name}')
    rankings = defaultdict(list)
    for model in tqdm(models, ncols=80):
        for idx, (reviewer, _) in enumerate(model.get_ranking(submission)):
            rankings[reviewer] += [idx+1]

    median_ranking, _ = zip(*sorted([ (reviewer, np.median(ranks)) for reviewer, ranks in rankings.items()], key=lambda x: x[1]))
    submissions_dir_ranking.joinpath(f'{submission.stem}.json').write_text(json.dumps(median_ranking, indent=4))