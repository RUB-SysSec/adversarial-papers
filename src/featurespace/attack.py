import json
import random
import time
from collections import defaultdict
from functools import partial
from pathlib import Path

import numpy as np
from autobid import AutoBid
from scipy.special import softmax

from .grid import create_candidate_grid
from .loss import loss as _loss
from .strategies.basic import BasicStrategy
from .strategies.predictive import PredictiveWordsStrategy
from .strategies.topic_based import TopicStrategy
from .strategies.word_based import WordStrategy
from .submission import Submission
from .utils import cluster, print_scores


def featurespace_attack(working_dir, logger, victim_models, surrogate_models, target, submission_words, submission_words_clean, features_blocked, config):
    submissions, victim_loss, loss = _featurespace_attack(working_dir, logger, victim_models, surrogate_models, target, submission_words, submission_words_clean, features_blocked, config)
    # loss = partial(_loss, autobid, config, target)

    if config['no_clusters'] is not None:
        no_clusters = min(config['no_clusters'], len(submissions))
        logger.info(f'\n    Cluster {len(submissions)} candidates into {no_clusters} cluster')
        submission_to_cluster_idx = cluster(submissions, no_clusters)
        submissions_ = []
        for cluster_idx in range(no_clusters):
            # get all submission in this cluster
            cluster_submissions = [ submission for submission_label, submission in zip(submission_to_cluster_idx, submissions) 
                                               if submission_label == cluster_idx ]
            # select submission with minimal loss
            losses = [ loss(submission) for submission in cluster_submissions ]
            best_submission_idx = np.argmin(losses)
            submissions_ += [cluster_submissions[best_submission_idx]]
            # log
            logger.info(f'\n[+] Cluster {cluster_idx}')
            for idx, (submission, submission_loss) in enumerate(zip(cluster_submissions, losses)):
                logger.info(f"    {'->' if idx == best_submission_idx else '  '} {submission_loss:7.4f} {json.dumps(submission.modified_words_cnt)[:128]}...")
        submissions = submissions_
    
    results = {
        'loss' : [ loss(submission) for submission in submissions ],
        'no_words' : [ len(submission.words) for submission in submissions ],
        'no_modified_words' : [ submission.no_modified_words for submission in submissions ],
        'l1' : [ submission.l1 for submission in submissions ],
        'linf' : [ submission.linf for submission in submissions ],
        'words_cnt' : [ submission._modified_words_cnt(skip_prior_modifiactions=True) for submission in submissions ]
    }

    return results

def surrogate_loss(loss_fn, config, target, submission):
    global surrogate_models
    loss = 0
    for surrogate_model in surrogate_models:
        loss += loss_fn(surrogate_model, config, target, submission)
    return loss

def _stop_condition(loss_fn, config, target, submission):
    global surrogate_models #, hold_out_surrogates, victim_model

    if config['stop_condition'] == 'all_successful':
        loss = [loss_fn(surrogate_model, config, target, submission) for surrogate_model in surrogate_models]
        return np.all(np.array(loss) <= config['delta'])
    
    elif config['stop_condition'] == 'one_successful':
        loss = [loss_fn(surrogate_model, config, target, submission) for surrogate_model in surrogate_models]
        return np.any(np.array(loss) <= config['delta'])

    elif config['stop_condition'] == 'majority_vote':
        loss = [loss_fn(surrogate_model, config, target, submission) for surrogate_model in surrogate_models]
        return np.sum(np.array(loss) <= config['delta']) >= (int(len(surrogate_models)/2)+1)
    
    elif config['stop_condition'] == 'victim':
        return loss_fn(victim_model, config, target, submission) < config['delta']

    elif config['stop_condition'] == 'hold_out_surrogates':
        loss = [loss_fn(surrogate_model, config, target, submission) for surrogate_model in hold_out_surrogates]
        return np.all(np.array(loss) <= config['delta'])

    else:
        raise ValueError(config['stop_condition'])


def _featurespace_attack(working_dir, logger, victim_models_, surrogate_models_, target, submission_words, submission_words_clean, features_blocked, config):

    global surrogate_models #, victim_models, hold_out_surrogates
    victim_models = victim_models_
    surrogate_models = surrogate_models_

    # Step 1: init strategies for adding/deleting words
    if config['strategy'] == 'basic':    
        strategies = { 'basic' : BasicStrategy(surrogate_models[0], features_blocked) }    
    elif config['strategy'] == 'aggregated':
        strategies = { 'aggregated' : PredictiveWordsStrategy(surrogate_models, config, features_blocked) }
    elif config['strategy'] == 'topic_based':
        strategies = { 'topic_based' : TopicStrategy(surrogate_models, config['omega'], features_blocked) }
    elif config['strategy'] == 'word_based':
        strategies = { 'word_based' : WordStrategy(surrogate_models, target, features_blocked, submission_words) }
    else:
        raise ValueError(config['strategy'])

    if config['strategy'] != 'aggregated':
        grid_size = len(list(strategies.items())[0][1].words)
        logger.info(f'\n[+] Grid size {grid_size}')
    else:
        grid_size = 0

    # Step 2: init loss
    loss_fn = _loss
    victim_loss = partial(loss_fn, victim_models[0], config, target)
    loss = partial(surrogate_loss, loss_fn, config, target)
    surrogate_losses = defaultdict(list)

    # Step 3: init stop condition
    if config['stop_condition'] == 'hold_out_surrogates':
        hold_out_surrogates = [ AutoBid(Path(model_dir)) for model_dir in config['hold_out_surrogates'] ]
    stop_condition = partial(_stop_condition, loss_fn, config, target)

    # Step 4: init submission
    submission = Submission(strategies, submission_words, submission_words_clean)

    logger.info(f"\n[+] Prior modifications")
    for word, cnt in submission.prior_modifications_cnt.items():
        logger.info(f"    {word:<20}: {cnt:<4}")

    # log parameters
    logger.info(f"\n[   0] {'Loss':<16}: {victim_loss(submission):3.2f}")
    logger.info(f'{submission}')

    # check if there is anything to do
    if stop_condition(submission):
        return [submission], victim_loss, loss

    if config['morphing']:
        assert len(target['request']) == 1 and len(target['reject']) == 0 and len(surrogate_models) == 1

        corpus_dir = Path(config['morphing_corpus_dir'])
        corpus =  { pdf.name : pdf for pdf in list(set(corpus_dir.rglob('*.pdf'))) }

        autobid = surrogate_models[0]
        
        model_idx = autobid.model_dir.relative_to(autobid.model_dir.parent.parent).as_posix()

        reviewer_to_papers = json.loads(Path(config['morphing_reviewer_to_papers']).read_text())[model_idx]
        try:
            papers = []
            for paper in reviewer_to_papers[target['request'][0]]:
                papers += [ AutoBid.parse_pdf_file(corpus[paper]) ]
        except KeyError:
            raise RuntimeError(f"Could not find papers for reviewer '{target['request'][0]}'")

        words = [ word for paper in set([tuple(paper) for paper in papers]) 
                       for word in paper
                       if word not in features_blocked ]

        itr = 0
        while loss(submission) > config['delta']:
            submission.extra_words += random.sample(words, config['step'])
            # log stats
            logger.info(f'\n[{itr+1:>4}] {"Loss":<16}: {loss(submission):3.2f}')
            logger.info(submission)
            print_scores(logger, autobid, submission, target)

            itr += 1

            if itr == 1000:
                break

        return [submission], victim_loss, loss
    
    # Step 5: bootstrap beam search
    grid = create_candidate_grid(surrogate_models, target, submission, config, grid_size, logger)
    submissions = submission.get_best_successors(grid, loss, config['beam_width'], config['max_inf_norm'], config['max_man_norm'])

    # break when there aren't any available successors
    if len(submissions) == 0:
        logger.info(f'\n[!] no successors')
        return [submission], victim_loss, loss

    logger.info(f'\n[{1:>4}] {"Loss":<16}: {victim_loss(submissions[0]):3.2f} - {victim_loss(submissions[-1]):3.2f}')
    logger.info(submissions[0])
    print_scores(logger, victim_models[0], submissions[0], target)

    # Step 6: optmize
    for itr in range(1, config['max_itr']):

        tic = time.time()

        # check if we done
        finished = [ stop_condition(submission) for submission in submissions ]
        if (    config['finish_all'] and np.all(finished)) or \
           (not config['finish_all'] and np.any(finished)):
            logger.info(f'\n[{itr+1:>4}] Success')
            break

        # get successors for each submission
        candidates = []
        for submission in submissions:
            grid = create_candidate_grid(surrogate_models, target, submission, config, grid_size, logger)
            candidates += submission.get_best_successors(grid, loss, config['beam_width'], config['max_inf_norm'], config['max_man_norm'])
    
        # de-duplicate
        candidates_unique = {}
        for candidate in candidates:
            key = hash(tuple(sorted(candidate.history)))
            candidates_unique[key] = candidate
        candidates_unique = list(candidates_unique.values())
        candidates_unique = [ (loss(candidate), candidate) for candidate in candidates_unique ]

        # remove candidates that are identical to a current submission
        candidates = []
        submission_cnts = [ submission.modified_words_cnt for submission in submissions ]
        for candidate_loss, candidate in candidates_unique:
            # cache words cnt
            candidate_cnt = candidate.modified_words_cnt
            # check submissions one by one
            for submission_cnt in submission_cnts:
                # check if submission and candidate contain the same words
                if set(submission_cnt.keys()) == set(candidate_cnt.keys()):
                    # if yes, check word cnts
                    for word, cnt in candidate.modified_words_cnt.items():
                        # break if there is at least one difference
                        # => continue w/ the next submission
                        if submission_cnt[word] != cnt:
                            break
                    else:
                        # candidate is identical to submission
                        # => break s.t. candidate is not added 
                        break
            else:
                # we did not break from loop
                # => there is no submission that is identical
                candidates += [(candidate_loss, candidate)]
        candidates_unique = candidates   

        if len(candidates_unique) == 0:
            logger.info(f'\n[{itr+1:>4}] No candidates left ({len(candidates_unique)} candidates)')
            break

        # select candidates
        if not config['regular_beam_search']:
            if len(candidates_unique) <= config['beam_width']:
                # continue with all remaining candidates
                candidates = candidates_unique

            else:
                # sample according to candidates loss
                # => *prefer* candidates with low loss
                loss_max = np.max([ loss for loss, _ in candidates_unique])
                loss_min = np.min([ loss for loss, _ in candidates_unique])
                probs = softmax([ (loss_max - loss) / (loss_max - loss_min) for loss, _ in candidates_unique])
                idxes = np.random.choice(len(candidates_unique), config['beam_width'], replace=False, p=probs)
                candidates = [ (loss, candidate) for idx, (loss, candidate) in enumerate(candidates_unique) 
                                                 if idx in idxes]
            # sort
            submissions = [ candidate for _, candidate in sorted(candidates, key=lambda x: x[0], reverse=False) ]

        else:
            # pick the best candidates
            candidates = sorted(candidates_unique, key=lambda x: x[0], reverse=False)
            submissions = [ candidate for _, candidate in candidates ][:config['beam_width']]

        # log stats
        logger.info(f'\n[{itr+1:>4}] {"Loss":<16}: {victim_loss(submissions[0]):3.2f} - {victim_loss(submissions[-1]):3.2f}')
        running_time = round(time.time() - tic, 2)
        logger.info(f'       {"Candidates":<16}: {len(submissions)} out of {len(candidates_unique)} unqiue candidates')
        logger.info(f'       {"Grid":<16}: {len(grid)}')
        logger.info(f'       {"Time":<16}: {running_time:3.2f}s')
        logger.info(submissions[0])
        surrogate_losses[-1] += [ victim_loss(submissions[0]) ]
        surrogate_loss_ = []
        for idx, surrogate_model in enumerate(surrogate_models):
            l = loss_fn(surrogate_model, config, target, submissions[0])
            surrogate_loss_ += [ f'{l:6.3f}' ]
            surrogate_losses[idx] += [l]
        logger.info(f'       {"Surrogates":<16}: {" ".join(surrogate_loss_)}')
        print_scores(logger, victim_models[0], submissions[0], target)
        working_dir.joinpath('surrogate_losses.json').write_text(json.dumps(surrogate_losses, indent=4))

    else:
        # reached max iteration
        logger.info(f'\n[{itr+1:>4}] Reached max iteration')
        pass

    return submissions, victim_loss, loss
