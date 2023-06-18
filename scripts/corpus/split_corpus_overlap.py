
from collections import defaultdict
from pdf_utils import analyze_words
from pathlib import Path
import numpy as np
import random
import shutil
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import json
from collections import defaultdict

random.seed(2022)

corpus_dir = Path.home() / "adversarial-papers" / "evaluation" / "corpus" / "oakland_22_large" / "archives"
corpus_out_dir = Path.home() / "adversarial-papers" / "evaluation" / "corpus" / "oakland_22_overlap"

if corpus_out_dir.is_dir():
    shutil.rmtree(corpus_out_dir)

# load reviewer archives
archives_dir = [ archive_dir for archive_dir in corpus_dir.glob('*') if archive_dir.is_dir() ]
archives_pdfs = {}
for archive_dir in archives_dir:
    archives_pdfs[archive_dir.name] = list(archive_dir.glob('*.pdf'))

# split data into two disjunct sets
corpus_victim = {}
corpus_surrogate_base = {}
for reviewer_name, reviewer_pdfs in archives_pdfs.items():
    corpus_victim[reviewer_name] = random.sample(reviewer_pdfs, k=len(reviewer_pdfs) // 2)
    corpus_surrogate_base[reviewer_name] = [ pdf_file for pdf_file in reviewer_pdfs
                                                      if pdf_file not in corpus_victim[reviewer_name] ]

corpus_size = len([pdf_file for pdf_files in corpus_victim.values() for pdf_file in pdf_files])
print(f'[+] Corpus size {corpus_size}')

# save victim corpus
corpus_victim_dir = corpus_out_dir.joinpath(f'victim', 'archives')
for reviewer_name, reviewer_pdfs in corpus_victim.items():
    corpus_victim_dir.joinpath(reviewer_name).mkdir(parents=True)
    for pdf_file in reviewer_pdfs:
        shutil.copyfile(pdf_file, corpus_victim_dir.joinpath(reviewer_name, pdf_file.name))

# for overlaps in 0.00, 0.10, ... , 1
for overlap in tqdm(np.arange(0, 1.1, 0.1), ncols=80):
    # sample overlap pdfs from victim
    overlap_size = int(corpus_size*overlap)
    corpus_victim_pdfs = [pdf_file for pdf_files in corpus_victim.values() for pdf_file in pdf_files]
    overlap_pdfs = list(random.sample(corpus_victim_pdfs, k=overlap_size))

    # sort overlap pdfs
    overlap_per_reviewer = defaultdict(list)
    for pdf in overlap_pdfs:
        overlap_per_reviewer[pdf.parent.name] += [pdf]

    # create surrogate corpus 
    corpus_surrogate = {}
    for reviewer_name, reviewer_pdfs in corpus_surrogate_base.items():
        # for each reviewer, use pdfs from overlap and fill up from surrogate base
        no_pdfs_in_overlap = len(overlap_per_reviewer[reviewer_name])
        no_pdfs_in_archive = len(corpus_victim[reviewer_name])
        corpus_surrogate[reviewer_name] = overlap_per_reviewer[reviewer_name] \
                                          + list(random.sample(corpus_surrogate_base[reviewer_name], k=no_pdfs_in_archive-no_pdfs_in_overlap))
        assert len(corpus_victim[reviewer_name]) == len(corpus_surrogate[reviewer_name])

    # check size
    assert len([pdf_file for pdf_files in corpus_victim.values()    for pdf_file in pdf_files]) == \
           len([pdf_file for pdf_files in corpus_surrogate.values() for pdf_file in pdf_files])
        
    # save surrogate corpus
    corpus_surrogate_dir = corpus_out_dir.joinpath(f'overlap_{overlap:.2f}', 'archives')
    for reviewer_name, reviewer_pdfs in corpus_victim.items():
        corpus_surrogate_dir.joinpath(reviewer_name).mkdir(parents=True)
        for pdf_file in reviewer_pdfs:
            shutil.copyfile(pdf_file, corpus_surrogate_dir.joinpath(reviewer_name, pdf_file.name))

# cache all corpusses
for corpus_dir in corpus_out_dir.glob('*'):
    print(corpus_dir)
    pdf_files = list({ pdf.name : pdf for pdf in corpus_dir.rglob('*.pdf') }.values())
    with Pool(cpu_count()) as p:
        words_per_pdf = p.imap(analyze_words, pdf_files, chunksize=1)
        corpus = [ words for words in tqdm(words_per_pdf, total=len(pdf_files), bar_format='    {l_bar}{bar:30}{r_bar}') ]
    corpus_dir.joinpath('corpus.json').write_text(json.dumps(corpus))
