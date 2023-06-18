
from pathlib import Path
from tqdm import tqdm
from autobid import AutoBid
from multiprocessing import Pool, cpu_count
import json

BASE_DIR = Path.home() / 'adversarial-papers'
CORPUS_BASE_DIR = BASE_DIR / 'evaluation' / 'corpus'

reviewer_load = 8 
paper_load = 5

print(f"[+] Load PDFs")
corpus_dir = CORPUS_BASE_DIR.joinpath(f'committees_base/archives')
corpus = sorted(corpus_dir.rglob('*.pdf'))
with Pool(80) as p:
    submissions = list(tqdm(p.imap(AutoBid.parse_pdf_file, corpus), ncols=80, total=len(corpus)))

CORPUS_BASE_DIR.joinpath('submissions').joinpath(f"committees_base.json").write_text(json.dumps(submissions))
