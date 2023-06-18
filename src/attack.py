# diasble numpy's internal multiprocessing
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import argparse
import copy
import json
import logging
import random
import shutil
import time
import typing
from copy import deepcopy
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import suppress
from pathlib import Path

import numpy as np
import pydng
from tqdm import tqdm

from autobid import AutoBid
from featurespace.attack import featurespace_attack
from problemspace.attackstrategy.Budgeting.ProblemSpaceCostBudgetManager import (
    CostBudget, ProblemSpaceCostBudgetManager)
from problemspace.attackstrategy.Budgeting.ProblemSpaceEqualBudgetManager import \
    ProblemSpaceEqualBudgetManager
from problemspace.attackstrategy.problemspace_attack import problemspace_attack
from problemspace.attackstrategy.RequestedChanges import RequestedChanges
from problemspace.PdfLatexSource import PdfLatexSource
from problemspace.transformers.TransformationState import TransformationState
from utils.pdf_utils import analyze_words
from utils.utils import (check_if_attack_is_successful,
                         compute_missing_changes, target_as_str)


def log_ranking(logger, ranking, target):
    for idx, (reviewer_name, score) in enumerate(ranking[:10]):
        if reviewer_name in target['request']:
            status = "^"
        elif reviewer_name in target['reject']:
            status = "v"
        else:
            status = ""
        if idx == 5:
            logger.info(f'      ---')
        logger.info(f'    {idx + 1:>2} {reviewer_name.upper().replace("_", " "):<20}: {score:.2f} {status}')


def single_feature_problem_space_iteration(iterationindex, adv_transfstate, logger, working_dir, victim_models, surrogate_models, 
                                           target, features_input, featurespace_config, problemspace_config,
                                           problemspacebudgetmanager, features_to_be_blocked, features_clean, clean_pdf_path) \
        -> typing.Tuple[int, typing.Optional[TransformationState], typing.List[str]]:
    iterationcomment: str = "" if iterationindex == 0 else f" (Iteration: {iterationindex})"
    feature_space_results_dir: Path = working_dir / "feature_space_results"
    feature_space_results_dir.mkdir(exist_ok=True, parents=True)

    # D. Feature-space attack
    logger.info(f"\n[+] Start attack in feature-space{iterationcomment}")
    logger.info(f"\n[+] Blocked features: {features_to_be_blocked}")

    feature_space_results: typing.Dict[str, list] = featurespace_attack(working_dir, logger, victim_models, surrogate_models, target, 
                                                                        features_input, features_clean, features_to_be_blocked, 
                                                                        featurespace_config)

    # pick feature vector
    # => just pick the best one (i.e., smallest loss)
    idx = np.argmin(feature_space_results['loss'])
    logger.info(f"\n[+] Pick feature vector {idx} with loss {feature_space_results['loss'][idx]:.2f}")
    requested_changes_best: typing.Dict[str, int] = feature_space_results['words_cnt'][idx]

    # get features
    features_adv = Counter(features_input)
    for word, cnt in requested_changes_best.items():
        features_adv[word] += cnt
        if features_adv[word] < 0:
            features_adv[word] = 0
    features_adv = [ word for word, cnt in features_adv.items() for _ in range(cnt) ]

    logger.info(f"\n[+] Ranking")
    ranking: typing.List[str, float] = victim_models[0].get_ranking(features_adv)
    log_ranking(logger, ranking, target)

    # check 
    results = check_if_attack_is_successful(clean=clean_pdf_path,
                                            adv=features_adv,
                                            target=target,
                                            models=victim_models)
    success = len([ r for r in results['successful'] if r == True ])
    failed = len([ r for r in results['successful'] if r == False ])
    invalid = len([ r for r in results['successful'] if r is None ])
    feature_space_results.update(results)

    feature_space_results_dir.joinpath(f'feature_space_results_{iterationindex}.json').write_text(
        json.dumps(feature_space_results, indent=4))
    logger.info(f"\n[+] Finished attack in feature-space{iterationcomment}")
    logger.info(f'    -> Success {success}\n    -> Failed {failed}\n    -> Invalid {invalid}')

    if featurespace_config['only_feature_space']:
        return -1, None, []

    # E. Problem-space attack
    logger.info(f"\n[+] Start attack in problem-space{iterationcomment}")
    requested_changes_problem_space: RequestedChanges = RequestedChanges(feature_space_results=feature_space_results,
                                                                         requested_changes_best=requested_changes_best,
                                                                         logger=logger)
    budget_for_iteration: typing.Dict[str, CostBudget] = problemspacebudgetmanager.\
        get_costbudget_for_iteration(iteration=iterationindex)

    adv_transfstate: TransformationState = problemspace_attack(logger=logger,
                                                              transfstate=adv_transfstate,
                                                              requested_changes=requested_changes_problem_space,
                                                              config=problemspace_config,
                                                              autobid_models=surrogate_models,
                                                              target=target,
                                                              clean_pdf_path=clean_pdf_path,
                                                              budget_for_iteration=budget_for_iteration,
                                                              working_dir=working_dir,
                                                              seed=41 + 100 * iterationindex)
    adv_pdf_path: Path = adv_transfstate.pdflatexsource.get_maindocument_pdf_path()
    logger.info(f"\n[+] Finished attack in problem-space{iterationcomment}")
    # # save adversarial project
    # adv_transfstate.pdflatexsource.copy_project_for_debugging(
    #     targetdir=working_dir / "adversarial_latex" / ("iteration_" + str(iterationindex)))

    # F. Test adversarial pdf
    features_adv: list = analyze_words(adv_pdf_path)
    logger.info("\n[+] Modifed words")
    added_words: Counter = Counter(features_adv) - Counter(features_input)
    added_words = sorted(added_words.items(), key=lambda x: x[1])
    deleted_words: Counter = Counter(features_input) - Counter(features_adv)
    deleted_words = sorted(deleted_words.items(), key=lambda x: x[1])

    logger.info("\n[+] Problem Space Restrictions: Feature Blocking")
    logger.info(f"\n[+] Blocked: {adv_transfstate.probspacerestrictions}")

    # check if we could realize all requested changes
    logger.info("\n[+] Missing changes")
    missing_changes_addition, missing_changes_deletion = compute_missing_changes(loggerobj=logger,
                                                                                 requested_changes=requested_changes_best,
                                                                                 added_words=added_words,
                                                                                 deleted_words=deleted_words)
    missing_changes = missing_changes_addition + missing_changes_deletion

    # get ranking, check if attack is successful for surrogates
    logger.info("\n[+] Ranking")
    results = check_if_attack_is_successful(clean=clean_pdf_path,
                                            adv=adv_pdf_path,
                                            target=target,
                                            models=surrogate_models)
    successful = len([ res for res in results['successful'] if res is not None]) == 0 or \
                 all([ res for res in results['successful'] if res is not None])
    ranking: typing.List[str, float] = victim_models[0].get_ranking(adv_pdf_path)
    log_ranking(logger, ranking, target)
    logger.info(f"\n[+] Evaluation on surrogates: {'Success' if successful else 'Failed'}")

    return int(successful), adv_transfstate, sorted(list(adv_transfstate.probspacerestrictions))

def attack(working_dir, victim_model_dirs, surrogate_model_dirs, submission, target_config, featurespace_config, problemspace_config):
    try:
        attack_start: float = time.time()

        # A. Setup logging
        working_dir.mkdir(exist_ok=True, parents=True)
        log_file: Path = working_dir / f'log.txt'
        if log_file.is_file(): log_file.unlink()
        logger: logging.Logger = logging.getLogger(working_dir.name)
        file_handler = logging.FileHandler(log_file.as_posix())
        file_handler.setFormatter(None)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.info(f"\n[+] Working dir @ {working_dir}")

        # B. Init AutoBid
        if 'featurespace_config' in target_config:
            featurespace_config = deepcopy(featurespace_config)
            featurespace_config.update(target_config['featurespace_config'])
            logger.info(f'\n[+] Update featurespace config\n   {json.dumps(featurespace_config)}')

        if 'problemspace_config' in target_config:
            problemspace_config = deepcopy(problemspace_config)
            problemspace_config.update(target_config['problemspace_config'])
            logger.info(f'\n[+] Update problemspace config\n   {json.dumps(problemspace_config)}')
        
        target = target_config['target_reviewer']

        victim_models = [ AutoBid(model_dir, lazy=True if idx != 0 else False) for idx, model_dir in enumerate(victim_model_dirs) ]
        logger.info('\n[+] Victim models')
        for victim_model in victim_models:
            logger.info(f'    {victim_model.model_dir}')

        surrogate_models = [ AutoBid(model_dir) for model_dir in surrogate_model_dirs ]
        logger.info('\n[+] Surrogate models')
        for surrogate_model in surrogate_models:
            logger.info(f'    {surrogate_model.model_dir}')

        # C. Prepare target submission
        original_pdflatexsource: PdfLatexSource = PdfLatexSource(latexsourcedir=submission,
                                                                 latexmainfilename="main.tex")

        # copy original project, as we will change the latex source
        pdflatexsource: PdfLatexSource = original_pdflatexsource.copyto()
        del original_pdflatexsource  # just to ensure we do not mess up with original files somehow

        # compile and save pdf
        pdflatexsource.runpdflatex()
        pdf_clean: Path = working_dir.joinpath('clean.pdf')
        shutil.copyfile(pdflatexsource.get_maindocument_pdf_path(), pdf_clean)

        # get features from submission
        features_clean: list = analyze_words(pdf_clean)
        logger.info(f"\n[+] {'Submission':<15}: {submission.stem}")
        logger.info(f"    {'Features':<15}: {len(features_clean)}")

        # log targets
        ranking: typing.List[str, float] = victim_models[0].get_ranking(pdf_clean)
        logger.info(f"    {'Requested':<15}: {' '.join(target['request'])}")
        logger.info(f"    {'Rejected':<15}: {' '.join(target['reject'])}")
        logger.info(f"\n[+] Initial Ranking")
        log_ranking(logger, ranking, target)

        # log config
        working_dir.joinpath('config.json').write_text(json.dumps({'submission': submission.as_posix(),
                                                                   'victim_model_dirs' : [ m.as_posix() for m in victim_model_dirs],
                                                                   'surrogate_model_dirs' : [ m.as_posix() for m in surrogate_model_dirs],
                                                                   'target': target,
                                                                   'featurespace_config': featurespace_config,
                                                                   'problemspace_config': problemspace_config},
                                                                   indent=4))

        # D. + E. Feature & Problem Space Attack
        # Either we perform feature-space attack first, and then problem-space attack
        # Or we switch between both iteratively.
        adv_features = copy.deepcopy(features_clean)
        start_adv_pdf_latexsource = pdflatexsource
        adv_transfstate: TransformationState = TransformationState(pdflatexsource=start_adv_pdf_latexsource)
        base_transfstate = adv_transfstate.copyto()  # let us save the original state for resetting if wanted

        # Budget.
        budget_transformers: typing.Dict[str, int] = {
            'BibTexTransformer': int(25 * problemspace_config['attack_budget']),
            'SynonymTransformer': int(25 * problemspace_config['attack_budget']),
            'FakeBibTexTransformer': int(5 * problemspace_config['attack_budget']),
            'SpellingMistakeTransformer': int(20 * problemspace_config['attack_budget']),
            'OurFinedTunedLangModelTransformer': int(10 * problemspace_config['attack_budget'])
        }
        cost_transformers: typing.Dict[str, float] = {
            'BibTexTransformer': 1,
            'SynonymTransformer': 2,
            'FakeBibTexTransformer': 2,
            'SpellingMistakeTransformer': 3,
            'OurFinedTunedLangModelTransformer': 10,
        }
        problemspacebudgetmanager: ProblemSpaceCostBudgetManager = ProblemSpaceEqualBudgetManager(
            budget_transformers=budget_transformers,
            cost_transformers=cost_transformers,
            feature_problem_switch=problemspace_config['feature_problem_switch'],
        )

        # Now perform attack
        # Feature Blocking
        features_to_be_blocked: typing.List[str] = []

        ix: int = 0
        while ix < problemspace_config['feature_problem_switch']:
            logger.info(f"\n\n{'#' * 3} ITERATION {ix:>3} {'#' * 70}\n")

            working_dir_itr = working_dir.joinpath('itrs', f'{ix}')
            working_dir_itr.mkdir(parents=True)

            is_successful, adv_transfstate, missing_changes = single_feature_problem_space_iteration(
                iterationindex=ix, adv_transfstate=adv_transfstate, logger=logger,
                working_dir=working_dir_itr, victim_models=victim_models, surrogate_models=surrogate_models,
                target=target, features_input=adv_features, featurespace_config=featurespace_config, 
                problemspace_config=problemspace_config, problemspacebudgetmanager=problemspacebudgetmanager, 
                features_clean=features_clean, features_to_be_blocked=features_to_be_blocked, clean_pdf_path=pdf_clean
            )
            if is_successful == -1:  # only-feature-space
                return
            adv_features: list = analyze_words(adv_transfstate.pdflatexsource.get_maindocument_pdf_path())
            if is_successful == 1:  # problem-space is successful, no further iterations necessary
                break

            ix += 1

            # Just update current iteration in transformation state to save debugging information
            adv_transfstate.history_group = str(ix)

            # Problem-Space Restrictions
            if problemspace_config['problem_space_block_features'] is True and len(missing_changes) > 0:
            # not all changes can be realized in problem space (e.g., words with unicode chars)
            # => block these words (transfer problem-space restrictions to the feature space)
                logger.info(f"\n[+] Added words to blocking list")
                features_to_be_blocked.extend(missing_changes)
                features_to_be_blocked = list(dict.fromkeys(features_to_be_blocked)) # avoid duplicates

            # Reset: not successful
            if ix == problemspace_config['feature_problem_switch'] and not is_successful:
                # reached muxed number of iterations, but attack was not successful
                # => try again
                logger.info(f"\n[+] Reset to initial state (not successful)")
                # reset working dir
                reset_dir = working_dir.joinpath('reset', 'not_successful')
                reset_dir.mkdir(exist_ok=True, parents=True)
                reset_ctr = len(list(reset_dir.glob('*')))
                logger.info(f"    -> reset no {reset_ctr}")
                if reset_ctr >= problemspace_config['repeat']:
                    break
                backup_dir = working_dir.joinpath('itrs').rename(reset_dir.joinpath(f'{reset_ctr}'))
                logger.info(f"    -> save state @ {backup_dir}")
                # reset transformation state
                adv_transfstate = base_transfstate.copyto() 
                adv_features = copy.deepcopy(features_clean)
                ix = 0

        adv_pdf_path: Path = adv_transfstate.pdflatexsource.get_maindocument_pdf_path()
        logger.info(f"\n[+] Finished attack in the feature and the problem space at iteration: {ix}")
        # save adversarial pdf and its latex project
        shutil.copyfile(adv_pdf_path, working_dir.joinpath('adversarial.pdf'))
        adv_transfstate.pdflatexsource.copy_project_for_debugging(
            targetdir=working_dir / "adversarial_latex" / "final")

        # F. Test adversarial pdf    
        features_adv: list = analyze_words(working_dir.joinpath('adversarial.pdf'))
        added_words: Counter = Counter(features_adv) - Counter(features_clean)
        deleted_words: Counter = Counter(features_clean) - Counter(features_adv)

        # norms
        modified_words = added_words + deleted_words
        l1 = sum([abs(cnt) for cnt in modified_words.values()])
        linf = max([abs(cnt) for cnt in modified_words.values()] + [0])
        logger.info(f"\n[+] L_1  : {l1}")
        logger.info(f"    L_inf: {linf}")

        # get ranking, check if successful
        logger.info("\n[+] Final Ranking")
        results = check_if_attack_is_successful(clean=working_dir.joinpath('clean.pdf'),
                                                adv=working_dir.joinpath('adversarial.pdf'),
                                                target=target,
                                                models=victim_models)
        ranking: typing.List[str, float] = victim_models[0].get_ranking(adv_pdf_path)
        log_ranking(logger, ranking, target)
        logger.info(f"\n[+] Final Evaluation")
        success = len([ r for r in results['successful'] if r == True ])
        failed = len([ r for r in results['successful'] if r == False ])
        invalid = len([ r for r in results['successful'] if r is None ])
        logger.info(f'    -> Success {success}\n    -> Failed {failed}\n    -> Invalid {invalid}')

        # running time
        running_time: int = round(time.time() - attack_start)
        logger.info(f"\n[+] Running time {running_time // 3600}h {(running_time % 3600) // 60}m {(running_time % 60)}s")

        # dump results
        results['feature_problem_switch'] = ix+1
        results['l1'] = l1
        results['linf'] =  linf
        results['running_time'] = running_time
        working_dir.joinpath('results.json').write_text(json.dumps(results, indent=4))

    except Exception as e:
        print(f"[!] Exception occured")
        print(f"    {working_dir}")
        import traceback
        print(traceback.format_exc())

def main(trial_name, trials_dir, models_dir, submissions_dir, workers, targets_file,
         featurespace_config, problemspace_config):

    # parse arguments
    print("[+] Parsed arguments")
    print(f'    - {"trial_name":<25}: {trial_name}')
    print(f'    - {"trials_dir":<25}: {trials_dir}')
    print(f'    - {"models_dir":<25}: {models_dir}')
    print(f'    - {"submissions_dir":<25}: {submissions_dir}')
    print(f'    - {"workers":<25}: {workers}')    
    print(f'    - {"targets_file":<25}: {targets_file}')
    print(f'    - {"workers":<25}: {workers}')
    print(f'    - {"featurespace_config":<25}')
    for name, value in featurespace_config.items():
        print(f'      - {name:<25}: {value}')
    print(f'    - {"problemspace_config":<25}')
    for name, value in problemspace_config.items():
        print(f'      - {name:<25}: {value}')

    # create a new process group
    # => all forked processes will be in this group
    with suppress(OSError):
        os.setsid()

    # overwrite trial dir, if neccessary
    trial_dir = trials_dir / trial_name
    if trial_dir.is_dir():
        print(f"[!] Trial dir already exists '{trial_dir}'")
        if input("    Enter yes to overwrite: ") == 'yes':
            print(f'    -> removed dir')
            shutil.rmtree(trial_dir)
        else:
            return

    # load targets
    targets = json.loads(targets_file.read_text())
    random.seed(2023)
    random.shuffle(targets)

    if workers == 1:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        logging.getLogger("utils.lda").setLevel(logging.WARNING)
        logging.getLogger("gensim").setLevel(logging.WARNING)

        # sequentially run attack for all targets
        for target_config in targets:
            # working dir
            working_dir = trial_dir / target_as_str(target_config)
            working_dir.mkdir(exist_ok=False, parents=True)
            # run the attack
            victim_model_dirs = [ models_dir.joinpath(m) for m in target_config['victim_models'] ]
            surrogate_model_dirs = [ models_dir.joinpath(m) for m in target_config['surrogate_models'] ]
            submission = submissions_dir.joinpath(target_config['submission'])
            attack(working_dir, victim_model_dirs, surrogate_model_dirs, submission,
                   target_config, featurespace_config, problemspace_config)


    else:
        logging.getLogger().addHandler(logging.NullHandler())
        futures = []
        with ProcessPoolExecutor(workers) as executor:
            print(f"[+] Schedule workers")

            # schedule attacks
            futures = []
            for target_config in targets:
                # working dir
                working_dir = trial_dir / target_as_str(target_config)
                working_dir.mkdir(exist_ok=False, parents=True)
                # submit
                victim_model_dirs = [ models_dir.joinpath(m) for m in target_config['victim_models'] ]
                surrogate_model_dirs = [ models_dir.joinpath(m) for m in target_config['surrogate_models'] ]
                submission = submissions_dir.joinpath(target_config['submission'])
                futures += [executor.submit(attack, working_dir, victim_model_dirs, surrogate_model_dirs, submission,
                                                    target_config, featurespace_config, problemspace_config)]

            print(f"[+] Attacks")
            for future in tqdm(as_completed(futures), bar_format='{l_bar}{bar:30}{r_bar}', total=len(futures)):
                future.result()  # check for exceptions
                pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial_name',
                        type=str,
                        default=f'{time.strftime("%Y-%m-%d")}_{pydng.generate_name()}',
                        help='Name of the trial')
    parser.add_argument('--trials_dir',
                        type=Path,
                        default=Path.home().joinpath('adversarial-papers', 'evaluation', 'trials'),
                        help='Base dir for storing results')
    parser.add_argument('--submissions_dir',
                        type=Path,
                        default=Path.home().joinpath('adversarial-papers', 'evaluation', 'submissions'),
                        help='Base dir for target submissions')
    parser.add_argument('--models_dir',
                        type=Path,
                        default=Path.home().joinpath('adversarial-papers', 'evaluation', 'models'),
                        help='Base dir for models')
    parser.add_argument('--workers',
                        type=int,
                        default=1,
                        help='Number of parallel instances. Each worker utilize one CPU.')
    parser.add_argument('--targets_file',
                        type=Path,
                        default=Path.home().joinpath('adversarial-papers', 'evaluation', 'targets', 'whitebox', 'targets_model.00_noselect.1_noreject.0_notargets.100.json'),
                        help='Path to the target file')

    feature_space_parser = parser.add_argument_group('featurespace_config', 'Parameters for Feature Space Attack')
    feature_space_parser.add_argument('--stop_condition', default='all_successful', type=str, 
                                      help='Stop condition for surrogate experiments. One of ["all_successful", "one_successful", "majority_vote", "victim", "hold_out_surrogates"]')
    feature_space_parser.add_argument('--hold_out_surrogates', type=str, nargs='+', default=[], 
                                      help='Used when stop_condition is "hold_out_surrogates"')
    # beam search
    feature_space_parser.add_argument('--max_itr', default=1000, type=int,
                                      help='Max number of iterations')
    feature_space_parser.add_argument('--delta', default=-0.02, type=float,
                                      help="Distance between target reviewers and remaining reviewers.")
    feature_space_parser.add_argument('--beam_width', type=int, default=1, 
                                      help='No of parallel candidates')
    feature_space_parser.add_argument('--step', default=64, type=int,
                                      help='No of words added in each iteration')
    feature_space_parser.add_argument('--no_successors', type=int, default=10000,
                                      help='Max number of successors')
    feature_space_parser.add_argument('--reviewer_window', type=int, default=9,
                                      help='Size of the reviewer window')
    feature_space_parser.add_argument('--reviewer_offset', type=int, default=1,
                                      help='Offset of the reviewer window')
    # topic distributions
    feature_space_parser.add_argument('--strategy', type=str, default='word_based',
                                      help='Strategy for adding/removing words. One of ["basic","aggregated","topic_based","word_based"]')
    feature_space_parser.add_argument('--lambda', type=float, default=0.8, 
                                      help='Hyperparameter for predictive words strategy')
    feature_space_parser.add_argument('--omega', type=float, default=1e-6, 
                                      help='Hyperparameter for predictive words strategy')
    # constraints
    feature_space_parser.add_argument('--max_man_norm', type=int, default=None,
                                      help="Limits the maximum number of modified words")
    feature_space_parser.add_argument('--max_inf_norm', type=int, default=None,
                                      help="Limits the maximum number on how often a single word can be added or removed")
    # general
    feature_space_parser.add_argument('--only_feature_space', action="store_true",
                                      help='Only perform feature-space attack')
    feature_space_parser.add_argument('--finish_all', action="store_true",
                                      help="Continue until all beam candidates are finished")
    feature_space_parser.add_argument('--no_clusters', type=int, default=None,
                                      help='Cluster similar candidates')
    # ablation
    feature_space_parser.add_argument('--all_topics', action="store_true",
                                      help='Consider all topics during candidate generation')
    feature_space_parser.add_argument('--regular_beam_search', action="store_true", 
                                       help="Flag to use a regular instead of stochastic beam search")
    # baseline
    feature_space_parser.add_argument('--morphing', action="store_true", 
                                     help='Flag to enable the morphing baseline')
    feature_space_parser.add_argument('--morphing_reviewer_to_papers', type=str, 
                                      default=Path.home().joinpath('adversarial-papers', 'scripts', 'morphing', 'reviewer_to_paper.json').as_posix(),
                                      help='Path to reviewer-paper mapping')
    feature_space_parser.add_argument('--morphing_corpus_dir', type=str, 
                                      default=Path.home().joinpath('adversarial-papers', 'evaluation', 'corpus', 'oakland_22_large').as_posix(),
                                      help='Path to document corpus')



    problem_space_parser = parser.add_argument_group('problemspace_config', 'Parameters for Problem Space Attack')
    # path information for loading necessary files
    problem_space_parser.add_argument('--bibtexfiles', type=str,
                                      default=Path.home().joinpath('adversarial-papers', 'evaluation', 'problemspace', 'bibsources').as_posix())
    problem_space_parser.add_argument('--synonym_model', type=str,
                                      default=Path.home().joinpath('adversarial-papers', 'evaluation', 'problemspace',
                                                                   'synonyms', 'committees_full-nostem.w2v.gz').as_posix(),
                                      help='Path to synonym model')
    problem_space_parser.add_argument('--stemming_map', type=str,
                                      default=Path.home().joinpath('adversarial-papers', 'src', 'problemspace', 'misc',
                                                                   'stemming_mapping').as_posix(),
                                      help='Path to directory that contains the stemming maps')
    problem_space_parser.add_argument('--lang_model_path', type=str,
                                      default=Path.home().joinpath('adversarial-papers', 'evaluation', 'problemspace', 'llms',
                                                                   'secpapermodels').as_posix(),
                                      help='Path to directory that contains the lang model (if self-finetuned model is used)')
    problem_space_parser.add_argument('--lang_model_key', type=str,
                                      default="facebook/opt-350m",
                                      help='Lang-Model key (if self-finetuned model is used)')
    # debugging
    problem_space_parser.add_argument('--debug_coloring', action="store_true")
    problem_space_parser.add_argument('--verbose', action="store_true")
    # general settings that influence attack procedure

    # allowed modifications
    problem_space_parser.add_argument('--text_level', action="store_true")
    problem_space_parser.add_argument('--encoding_level', action="store_true")
    problem_space_parser.add_argument('--format_level', action="store_true")
    # strategy adjustments
    problem_space_parser.add_argument('--problem_space_finish_all', action="store_true",
                                      help="Attack tries multiple targets from feature space")
    problem_space_parser.add_argument('--feature_problem_switch', type=int, default=1,
                                      help='How often do we switch between feature and problem space')
    problem_space_parser.add_argument('--problem_space_block_features', action="store_true",
                                      help="Problem-space strategy selects features that are blocked in feature-space")
    problem_space_parser.add_argument('--attack_budget', type=float, default=1,
                                      help='Scalar for attack budget')
    problem_space_parser.add_argument('--repeat', type=int, default=0,
                                    help='Number of repetitions if attack fails')

    # parse and group arguments
    # -> args w/o group are added directly to result dict
    # -> args w/  group are first merged together
    args = parser.parse_args()
    args_dict = {}
    for group in parser._action_groups:  # dirty, but argparse does not support this natively
        group_dict = {a.dest: getattr(args, a.dest, None) for a in group._group_actions}
        if group.title in ["positional arguments", "optional arguments"]:
            # args w/o group 
            args_dict.update(group_dict)
        else:
            # args w/ group
            args_dict[group.title] = group_dict
    del args_dict['help']

    # call main with parsed arguments
    main(**args_dict)

    #
    # PROFILING
    #

    # import cProfile
    # import io
    # import pstats
    # pr = cProfile.Profile()
    # pr.enable()
    # try:
    #     main(**args_dict)
    # except KeyboardInterrupt:
    #     pass
    # pr.disable()
    # s = io.StringIO()
    # sortby = 'cumulative'
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # print(s.getvalue())
