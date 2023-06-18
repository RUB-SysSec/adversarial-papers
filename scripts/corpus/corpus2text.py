
from re import L
import sys
from pathlib import Path

sys.path.append(Path.home().joinpath('adversarial-papers', 'src').as_posix())  

from utils.pdf_utils import scrape_via_pdftotext
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import json

def load_pdf(pdf_file):
    return (pdf_file.stem, scrape_via_pdftotext(pdf_file))

corpus2text_dir = Path.home().joinpath('adversarial-papers/evaluation/corpus/corpus2text')
corpus2text_dir.mkdir(exist_ok=True, parents=True)

corpus_dirs = {
    'sp_full' : Path.home().joinpath('adversarial-papers/evaluation/corpus/oakland_22_base/archives'),
    'sp_blackbox' : Path.home().joinpath('adversarial-papers/evaluation/corpus/oakland_22/overlap_0.00'),
    'committees_full' : Path.home().joinpath('adversarial-papers/evaluation/corpus/committees_base/archives')
}

for corpus_name, corpus_dir in corpus_dirs.items():
    print(f'[+] {corpus_name}')
    corpus2text_file = corpus2text_dir.joinpath(f'{corpus_name}.json')
    if corpus2text_file.is_file():
        texts = json.loads(corpus2text_file.read_text())
    else:
        pdf_files = sorted(corpus_dir.rglob("*.pdf"))
        print(f'    PDF files: {len(pdf_files)}')
        with Pool(80) as p:
            texts = dict(tqdm(p.imap(load_pdf, pdf_files), ncols=80, total=len(pdf_files)))
        corpus2text_file.write_text(json.dumps(texts, indent=4))
    print(f'    texts: {len(texts)}')


import json
from pathlib import Path
corpus = Path.home().joinpath('adversarial-papers/evaluation/corpus/corpus2text/committees_full.json')
papers = json.loads(corpus.read_text())
for paper_hash, paper_body in papers.items():
    print(f'{paper_hash}: {len(paper_body)}')

