import sys
from pathlib import Path
sys.path.append(Path.home().joinpath('adversarial-papers', 'src').as_posix()) 
from autobid import AutoBid
from utils.pdf_utils import analyze_words

import argparse
import json
import random
import re
from collections import defaultdict
from contextlib import redirect_stderr, redirect_stdout
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from pulp import *
from tqdm import tqdm


from config import *
from trial import Trial

def get_assignment(similarity_matrix, n_reviewers, n_papers, reviewer_load=3, paper_load=5):
    with redirect_stderr(open(os.devnull, 'w')):
        with redirect_stdout(open(os.devnull, 'w')):
            model = LpProblem("Assignments", LpMaximize)
            variable_names = ['r'+str(r)+'p'+str(p) for r in range(n_reviewers) for p in range(n_papers)]

            DV_variables = LpVariable.matrix("X", variable_names, cat="Integer", lowBound=0, upBound=1)
            allocation = np.array(DV_variables).reshape(n_reviewers,n_papers)

            obj_func = lpSum(allocation*similarity_matrix)
            model +=  obj_func

            for p in range(n_papers):
                model += lpSum(allocation[r][p] for r in range(n_reviewers)) == paper_load


            for r in range(n_reviewers):
                model += lpSum(allocation[r][p] for p in range(n_papers)) <= reviewer_load

            model.solve()

            status =  LpStatus[model.status]
            print(status)
            print("Total Cost:", model.objective.value())

            papers_to_reviewers = defaultdict(list)
            for v in model.variables():
                if v.value() == 1:
                    r, p = re.findall(r'r(\d+)p(\d+)', v.name)[0]
                    papers_to_reviewers[int(p)] += [int(r)]

            papers_to_reviewers = dict(sorted(papers_to_reviewers.items(), key=lambda x: int(x[0])))
            for r in range(n_reviewers):
                hits = 0
                for p in range(n_papers):
                    if r in papers_to_reviewers[p]:
                        hits += 1
                assert hits <= reviewer_load
            
            return papers_to_reviewers

def check_assignment(name):
    global TRIAL_DIR, CORPUS_BASE_DIR, MODELS_BASE_DIR, REVIEWER_LOAD, PAPER_LOAD, SUBMISSIONS

    subtrial_dir = TRIAL_DIR.joinpath(name)

    # parse
    no_reviewer, margin, model_idx = re.findall(r'reviewers.(\d+)__margin.(.*)__.*__victim\.(\d+)', name).pop()
    no_reviewer = int(no_reviewer)
    margin = float(margin)

    # config
    config = json.loads(subtrial_dir.joinpath('config.json').read_text())

    # load model
    model = AutoBid(Path(config['victim_model_dirs'][0]))
    
    # load submissions
    no_submissions = (REVIEWER_LOAD*no_reviewer)//PAPER_LOAD    
    submissions = random.sample(SUBMISSIONS, k=no_submissions-1)

    # target reviwer
    target_reviewer = model.reviewers_list.index(config['target']['request'][0])

    # init similarity matrix
    similarity_matrix = np.zeros((no_reviewer, no_submissions))
    for p, words in enumerate(submissions):
        similarity_matrix[:, p] = model.get_scores(words)

    # assignment before
    clean = AutoBid.parse_pdf_file(subtrial_dir.joinpath('clean.pdf'))
    similarity_matrix[:, no_submissions-1] = model.get_scores(clean)
    assignment_before = get_assignment(similarity_matrix, no_reviewer, no_submissions, REVIEWER_LOAD, PAPER_LOAD)[no_submissions-1]

    if (target_reviewer in assignment_before):
        return no_reviewer, margin, model_idx, "invalid"

    # assignment after
    adversarial = AutoBid.parse_pdf_file(subtrial_dir.joinpath('adversarial.pdf'))
    similarity_matrix[:, no_submissions-1] = model.get_scores(adversarial)
    assignment_after = get_assignment(similarity_matrix, no_reviewer, no_submissions, REVIEWER_LOAD, PAPER_LOAD)[no_submissions-1]

    # check
    if target_reviewer in assignment_after:
        return no_reviewer, margin, model_idx, "success"
    else:
        return no_reviewer, margin, model_idx, "failed"

random.seed(2022)

parser = argparse.ArgumentParser()
parser.add_argument('--trials_dir', type=Path, nargs='+')
parser.add_argument('--name', type=str)
parser.add_argument('--workers', default=32, type=int)
args = parser.parse_args()

print(args.trials_dir)
print(args.workers)

BASE_DIR = Path.home() / 'adversarial-papers'
CORPUS_BASE_DIR = BASE_DIR / 'evaluation' / 'corpus'
MODELS_BASE_DIR = BASE_DIR / 'evaluation' / 'models'
TRIALS_DIR = BASE_DIR / 'evaluation' / 'trials'

REVIEWER_LOAD = 10
PAPER_LOAD = 5

SUBMISSIONS = json.loads(BASE_DIR.joinpath('evaluation/corpus/committees_base.json').read_text())
SUBMISSIONS = sorted(list({ tuple(submission) for submission in SUBMISSIONS }))

results = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

for TRIAL_DIR in args.trials_dir:
    trial = Trial(TRIAL_DIR, TRIAL_DIR.name, only_featurespace=False)
    with Pool(args.workers) as p:
        for no_reviewer, margin, model_idx, result in tqdm(p.imap(check_assignment, trial.config), total=len(trial.config), ncols=80):
            results[no_reviewer][margin][model_idx][result] += 1
            TRIALS_DIR.joinpath(f'{args.name}.json').write_text(json.dumps(results, indent=4))
