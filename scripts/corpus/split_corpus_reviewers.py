from pathlib import Path
import random
import shutil
from tqdm import tqdm

random.seed(2022)

no_committees_per_size = 8

corpus_dir = Path.home() / "adversarial-papers" / "evaluation" / "corpus" / "large" / "archives"
corpus_out_dir_base = Path.home() / "adversarial-papers" / "evaluation" / "corpus" / "committees"

reviewer_archives = sorted([ archive_dir for archive_dir in corpus_dir.glob("*") if archive_dir.is_dir() ])

for no_reviewers in range(50, 550, 50):
    print(f'[+] Reviewers {no_reviewers}')

    for committee_idx in range(no_committees_per_size):
        reviewer_archives_subset = random.sample(reviewer_archives, k=no_reviewers)
        corpus_out_dir = corpus_out_dir_base.joinpath(f'{no_reviewers}', f'{committee_idx:>02}', 'archives')

        if corpus_out_dir.is_dir():
            print(f'[!] {corpus_out_dir} exists')
            continue
            shutil.rmtree(corpus_out_dir)

        corpus_out_dir.mkdir(parents=True)

        for reviewer_archive in tqdm(reviewer_archives_subset, ncols=80):
            shutil.copytree(reviewer_archive, corpus_out_dir.joinpath(reviewer_archive.name))

        # print(corpus_out_dir)