import logging
import random
import typing
from itertools import chain, combinations
from pathlib import Path

from autobid import AutoBid
from problemspace.PdfLatexSource import PdfLatexSource
from tqdm import tqdm


def init_logger(name, log_dir):
    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / f'{name}_log.txt'
    if log_file.is_file(): log_file.unlink()
    logger = logging.getLogger(name)
    file_handler = logging.FileHandler(log_file.as_posix())
    file_handler.setFormatter(None)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.info(f"\n[+] Logging to {log_file.name}")
    return logger

def cleanup(data_dir):
    files = []
    files += [ data_dir.joinpath('corpus.json') ]
    files += [ data_dir.joinpath('reviewers.json') ]
    files += [ data_dir.joinpath('submissions.json') ]
    files += [ data_dir.joinpath('scores_dirichlet_smoothed_word_counts.json') ]
    files += [ data_dir.joinpath('scores_lda.json') ]
    files += [ data_dir.joinpath('scores_normalized_word_counts.json') ]
    
    archives_dir = data_dir / 'archives'
    files += [ archives_dir.joinpath('lda.model') ] 
    files += [ archives_dir.joinpath('lda.model.expElogbeta.npy') ]
    files += [ archives_dir.joinpath('lda.model.id2word') ]
    files += [ archives_dir.joinpath('lda.model.state') ]

    print(f"[+] Cleanup")
    for f in files:
        if f.is_file(): 
            print(f"    {f}")
            f.unlink()

def log_submission_topics(prev_topics, current_topics, target_topics):
    print(f'[+] ID TARGET  PREV    CURRENT')
    topic_ids = sorted(set(chain(prev_topics, current_topics, target_topics)))
    for topic_id in topic_ids:
        target = f'{target_topics[topic_id]:7.5f}' if topic_id in target_topics else "n/a"
        prev = f'{prev_topics[topic_id]:7.5f}' if topic_id in prev_topics else "n/a"
        current = f'{current_topics[topic_id]:7.5f}' if topic_id in current_topics else "n/a"
        try:
            delta = current_topics[topic_id] - prev_topics[topic_id]
            delta = f'{delta:+7.5f}'
        except KeyError:
            delta = ""
        print(f'    {topic_id:>02} {target:>7} {prev:>7} {current:>7} ({delta})')

def check_if_attack_is_successful(clean: Path, adv: typing.Union[Path, typing.List[str]], target: dict, models: typing.List[AutoBid]) \
        -> typing.Tuple[typing.List[typing.Tuple[str, float]], bool]:
    """
    Checks if the attack against the AutoBid systems are successful.
    """

    results = {
        'successful' : [],
        'ranks': [] 
    }

    if isinstance(adv, Path):
        features_adv = AutoBid.parse_pdf_file(adv)
    else:
        features_adv = adv

    for model in models:

        # 1. check if clean pdf was already succesful
        rankings_clean: typing.List[typing.Tuple[str, float]] = model.get_ranking(clean)
        reviewer_to_ranks_clean: typing.Dict[str, int] = { name : idx for idx, (name, _) in enumerate(rankings_clean) }
        requests_done = all([ (reviewer_to_ranks_clean[r] <  5) for r in target['request'] ]) if len(target['request']) > 0 else True
        rejects_done  = all([ (reviewer_to_ranks_clean[r] >= 5) for r in target['reject']  ]) if len(target['reject'])  > 0 else True
        is_successful = (requests_done and rejects_done)

        if is_successful:
            # if so, don't count this model
            results['successful'] += [ None ]
            results['ranks'] += [ None ]
            continue
        
        # 2. check adversarial
        rankings_adv: typing.List[typing.Tuple[str, float]] = model.get_ranking(features_adv)
        reviewer_to_ranks_adv: typing.Dict[str, int] = { name : idx for idx, (name, _) in enumerate(rankings_adv) }
        requests_done = all([ (reviewer_to_ranks_adv[r] <  5) for r in target['request'] ]) if len(target['request']) > 0 else True
        rejects_done  = all([ (reviewer_to_ranks_adv[r] >= 5) for r in target['reject']  ]) if len(target['reject'])  > 0 else True
        is_successful = (requests_done and rejects_done)
        results['successful'] += [ is_successful ]

        # 3. count rank difference
        ranks = { 'request' : {}, 'reject' : {} }
        for r in target['request']:
            ranks['request'][r] = reviewer_to_ranks_clean[r] - reviewer_to_ranks_adv[r]
        for r in target['reject']:
            ranks['reject'][r] = reviewer_to_ranks_clean[r] - reviewer_to_ranks_adv[r]
        results['ranks'] += [ ranks ]

    return results

def target_as_str(target):
    prefix = target['working_dir_prefix']+'__' if 'working_dir_prefix' in target else ""
    return f'{prefix}{target["submission"].split("/")[-1]}__victim.{"_".join([m.split("/")[-1] for m in target["victim_models"]])}__surrogate.{"_".join([m.split("/")[-1] for m in target["surrogate_models"]])}__select.{"_".join(target["target_reviewer"]["request"])}__reject.{"_".join(target["target_reviewer"]["reject"])}'

def compute_missing_changes(loggerobj, requested_changes, added_words, deleted_words):
    missing_changes_addition = []
    missing_changes_deletion = []

    added_words = dict(added_words)
    for word, cnt in requested_changes.items():
        if cnt > 0:
            try:
                if added_words[word] != cnt:
                    loggerobj.info(f"    {word:<20}: {added_words[word]:<4} != {cnt:<4}")
                    missing_changes_addition.append(word)
            except KeyError:
                # word is missing
                loggerobj.info(f"    {word:<20}: {'0':<4} != {cnt:<4}")
                missing_changes_addition.append(word)

    deleted_words = dict(deleted_words)
    for word, cnt in requested_changes.items():
        if cnt < 0:
            try:
                if deleted_words[word] != cnt:
                    loggerobj.info(f"    {word:<20}: {deleted_words[word]:<4} != {cnt:<4}")
                    missing_changes_deletion.append(word)
            except KeyError:
                # word is missing
                loggerobj.info(f"    {word:<20}: {'0':<4} != {cnt:<4}")
                missing_changes_deletion.append(word)

    return missing_changes_addition, missing_changes_deletion
