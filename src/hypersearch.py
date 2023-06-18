import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import argparse
import json
import logging
import random
import time
import traceback
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from contextlib import redirect_stderr, redirect_stdout, suppress
from itertools import product
from multiprocessing import Process
from pathlib import Path
from tempfile import TemporaryDirectory
import re
import numpy as np
import pandas as pd
import signal
from attack import main


def append_to_dataframe(df, element):
    # add element
    df = df.append(element, ignore_index=True)
    # sort data frame
    df = df.sort_values(['finished', 'failed', 'median', 'mean'], ascending=[False, True, True, True])
    df = df.reset_index(drop=True)
    # find element
    rank = [int(idx)+1 for idx in df.index if dict(df.loc[idx]) == element]; 

    if len(rank) != 1:
        print(df)
        print(element)
        print(rank)

    return df, rank.pop()

def run_trial(config, targets, featurespace_config, max_time):
    with redirect_stderr(open(os.devnull, 'w')):
        with redirect_stdout(open(os.devnull, 'w')):
            with TemporaryDirectory() as trials_dir:
                targets_file = Path(trials_dir) / 'targets.json'
                targets_file.write_text(json.dumps(targets))
                config['trials_dir'] = Path(trials_dir)
                config['featurespace_config'] = featurespace_config
                config['targets_file'] = targets_file

                tic = time.time()
                p = Process(target=main, kwargs=config)
                p.start()
                print(p.pid)
                p.join(timeout=max_time)
                with suppress(OSError):
                    os.killpg(p.pid, signal.SIGKILL)
                # p.kill()      
                running_time = round(time.time() - tic)

                # analyze
                finished = 0 
                failed = 0
                words = []
                for log_file in Path(trials_dir).rglob('log.txt'):
                    feature_space_results = list(log_file.parent.rglob('feature_space_results*.json'))
                    assert len(feature_space_results) <= 1, len(feature_space_results)

                    # finished?
                    if len(feature_space_results) == 0:
                        continue
                    finished += 1
                    
                    # load featurespace results
                    feature_space_results = feature_space_results[0]
                    feature_space_results = json.loads(feature_space_results.read_text())  

                    # trivial?
                    if len([ r for r in feature_space_results['successful'] if r is None]) == len(feature_space_results['successful']):
                        continue
                    
                    # successful?
                    no_failed = len([ r for r in feature_space_results['successful'] if r == False])

                    # if no_success == 0:
                    failed += no_failed

                    # words?
                    words += [ min(feature_space_results['l1']) ]

                median = int(np.median(words)) if len(words) > 0 else np.inf
                mean = int(np.mean(words)) if len(words) > 0 else np.inf
                return finished, failed, median, mean, running_time

def hypersearch(**kwargs):

    print("[+] Parsed arguments")
    print(f'    - {"name":<25}: {kwargs["name"]}')
    print(f'    - {"workers":<25}: {kwargs["workers"]}')
    print(f'    - {"workers_per_trial":<25}: {kwargs["workers_per_trial"]}')
    print(f'    - {"white_box":<25}: {kwargs["white_box"]}')
    print(f'    - {"black_box":<25}: {kwargs["black_box"]}')
    print(f'    - {"no_targets":<25}: {kwargs["no_targets"]}')
    print(f'    - {"trials_dir":<25}: {kwargs["trials_dir"]}')
    print(f'    - {"timeout":<25}: {kwargs["timeout"]}')
    print(f'    - {"grid":<25}')
    print(f'      * {"beam_width":<23}: {kwargs["beam_width"]}')
    print(f'      * {"step":<23}: {kwargs["step"]}')
    print(f'      * {"delta":<23}: {kwargs["delta"]}')
    print(f'      * {"reviewer_window":<23}: {kwargs["reviewer_window"]}')
    print(f'      * {"reviewer_offset":<23}: {kwargs["reviewer_offset"]}')

    kwargs['trials_dir'].mkdir(exist_ok=True, parents=True)
    #
    # FIXED PARAMETER
    #

    config = {
        'trial_name' : 'default', 
        'trials_dir' : None,
        'submissions_dir' : Path.home().joinpath('adversarial-papers', 'evaluation', 'submissions'),
        'models_dir' : Path.home().joinpath('adversarial-papers', 'evaluation', 'models'),
        'workers' : kwargs['workers_per_trial'], 
        'targets_file' : None,
        'problemspace_config' : {
            "bibtexfiles": "/root/adversarial-papers/evaluation/problemspace/bibsources",
            "synonym_model": "/root/adversarial-papers/evaluation/problemspace/synonyms/sec-conf-paper-nostem.w2v.gz",
            "stemming_map": "/root/adversarial-papers/src/problemspace/misc/stemming_mapping",
            "debug_coloring": False,
            "verbose": False,
            "problem_space_attack_strategy": 1,
            "problem_space_finish_all": False,
            "feature_problem_switch": 1,
            "problem_space_block_features": False,
            "attack_budget": 1,
            "repeat": 0,
            "text_level": False,
            "encoding_level": False,
            "format_level": False
        }       
    }

    if kwargs["white_box"]:
        targets_file = Path.home().joinpath('adversarial-papers', 'evaluation', 'targets', 'hypersearch', 'targets_hypersearch_whitebox.json')
        kwargs["name"] = 'whitebox' if len(kwargs["name"]) == 0 else kwargs["name"]

    elif kwargs["black_box"]:
        targets_file = Path.home().joinpath('adversarial-papers', 'evaluation', 'targets', 'hypersearch', 'targets_hypersearch_blackbox.json')
        kwargs["name"] = 'blackbox' if len(kwargs["name"]) == 0 else kwargs["name"]

    else:
        raise ValueError("[!] No config")

    #
    # TARGETS
    #

    targets_all = json.loads(targets_file.read_text())
    random.seed(2022)
    targets = random.sample(targets_all, min(len(targets_all), kwargs['no_targets']))

    #
    # FEATURESPACE CONFIG
    #

    parameters_fixed = {
        'max_rank' : False,
        "stop_condition": "all_successful",
        "hold_out_surrogates": [],
        "max_itr": 1000,
        "lambda": 0.8,
        "omega": 1e-06,
        "strategy": "word_based",
        "max_man_norm": None,
        "max_inf_norm": None,
        "only_feature_space": True,
        "finish_all": False,
        "no_clusters": None,
        "transferability": False,
        "all_topics": False,
        "regular_beam_search": False,
        "only_basic_words": False,
        "baseline": False
    }

    parameters_variable_grid = {
        "beam_width"      : kwargs['beam_width'],
        "step"            : kwargs['step'],
        "delta"           : kwargs['delta'],
        "reviewer_window" : kwargs['reviewer_window'],
        "reviewer_offset" : kwargs['reviewer_offset'],
        "no_successors"   : kwargs['no_successors']
    }

    featurespace_config_grid = []
    for parameter_variable in product(*tuple(parameters_variable_grid.values())):
        parameters = { name: value for name, value in zip(parameters_variable_grid, parameter_variable) }
        parameters.update(parameters_fixed)
        featurespace_config_grid += [parameters]
    grid_size = len(featurespace_config_grid)

    random.seed(2022)
    random.shuffle(featurespace_config_grid)

    #
    # SEARCH
    #

    logging.getLogger().addHandler(logging.NullHandler())
    results = pd.DataFrame(columns=['failed', 'finished', 'median', 'mean'] + list(parameters_variable_grid.keys()))

    with ProcessPoolExecutor(kwargs['workers'] // kwargs['workers_per_trial']) as executor:

        futures = {}
        
        # init
        for _ in range(kwargs['workers'] // kwargs['workers_per_trial']):
            featurespace_config = featurespace_config_grid.pop()
            future = executor.submit(run_trial, config, targets, featurespace_config, kwargs['timeout'])
            futures[future] = featurespace_config

        # while not done
        while len(futures) > 0:
            # wait for job to finish
            done, not_done = wait(futures, return_when=FIRST_COMPLETED)
            # remove finished jobs from futures dict
            new_futures = { future : futures[future] for future in not_done }
            # iterate over finished jobs
            for future in done:
                # get results
                try:
                    finished, failed, median, mean, running_time = future.result()

                    result = {
                        key : value for key, value in futures[future].items()
                        if key in parameters_variable_grid
                    }
                    result['finished'] = finished
                    result['failed'] = failed
                    result['median'] = median
                    result['mean'] = mean
                    result['running_time'] = running_time
                    
                    # save result and get rank
                    results, rank = append_to_dataframe(results, result)
                    print(f"\n[+] Finished with rank {rank}: {result}")

                except Exception as e:
                    finished, failed, median, mean, running_time = np.nan, np.nan, np.nan, np.nan, np.nan
                    print(f"[!] Error for {futures[future]}")
                    traceback.print_exc()
 
                # get new candidate
                if len(featurespace_config_grid) == 0:
                    print(f'\n[+] No candidates left')
                    continue
                featurespace_config = featurespace_config_grid.pop()

                # submit
                future = executor.submit(run_trial, config, targets, featurespace_config, kwargs['timeout'])
                new_futures[future] = featurespace_config

            # update  
            futures = new_futures
                
            # dump
            kwargs['trials_dir'].joinpath(f'{kwargs["name"]}.json').write_text(results.to_json())
            kwargs['trials_dir'].joinpath(f'{kwargs["name"]}.txt').write_text(results.to_string())
            print(f"\n[+] Hyperparameter Search ({len(results)} / {grid_size} completed)")
            for line in str(results).splitlines():
                print(f'    {line}')

            
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--name', 
                        type=str,
                        default=f'',
                        help='')

    parser.add_argument('--white_box', action="store_true")
    parser.add_argument('--black_box', action="store_true")

    parser.add_argument('--workers', 
                        type=int, 
                        default=104,
                        help='')

    parser.add_argument('--workers_per_trial', 
                        type=int, 
                        default=8,
                        help='')

    parser.add_argument('--no_targets', 
                        type=int, 
                        default=1000,
                        help='')

    parser.add_argument('--trials_dir', 
                        type=Path, 
                        default=Path.home().joinpath('adversarial-papers', 'evaluation', 'trials', '_hyperparameter'),
                        help='')

    parser.add_argument('--beam_width', 
                        type=int, 
                        default=[1, 2, 4, 8],
                        nargs='+',
                        help='')
                            
    parser.add_argument('--step', 
                        type=int, 
                        default=[32, 64, 128, 256],
                        nargs='+',
                        help='')
    parser.add_argument('--delta', 
                        type=float, 
                        default=[0, -0.01, -0.02, -0.04, -0.08, -0.16],
                        nargs='+',
                        help='')

    parser.add_argument('--reviewer_window', 
                        type=int, 
                        default=[2, 4, 6, 8],
                        nargs='+',
                        help='')

    parser.add_argument('--reviewer_offset', 
                        type=int, 
                        default=[0, 1, 2, 3],
                        nargs='+',
                        help='')
    
    parser.add_argument('--no_successors', 
                        type=int, 
                        default=[128, 256, 512],
                        nargs='+',
                        help='')

    parser.add_argument('--timeout', 
                    type=int, 
                    default=28800,
                    help='')


    # parse and group arguments
    # -> args w/o group are added directly to result dict
    # -> args w/  group are first merged together
    args = parser.parse_args()
    args_dict = {}
    for group in parser._action_groups: # dirty, but argparse does not support this natively
        group_dict = { a.dest:getattr(args, a.dest, None) for a in group._group_actions }
        if group.title in ["positional arguments", "optional arguments"]:
            # args w/o group 
            args_dict.update(group_dict)
        else:
            # args w/ group
            args_dict[group.title] = group_dict
    del args_dict['help']

    # call main with parsed arguments
    hypersearch(**args_dict)
