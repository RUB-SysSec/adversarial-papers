import random
from itertools import combinations, chain

def create_candidate_grid(surrogate_models, target, submission, config, grid_size, logger):

    if config['strategy'] == 'aggregated':

        assert len(surrogate_models) == 1
        autobid = surrogate_models[0]

        reviewer_topics = set()
        submission_topics = set()

        ranking = autobid.get_ranking(submission.words)

        # reviewer topics := union of topics over all/top 10 of reviewer
        # => used for adding words
        reviewer_topics = []
        if config['all_topics']:
            reviewer_topics = range(50)

        else:
            top_10 = [ name for name, _ in ranking[:10]]
            for reviewer_name in top_10:
                _, r_topics = autobid.get_reviewer(reviewer_name)
                reviewer_topics += [ topic_id for topic_id, prob in enumerate(r_topics) if prob > 0] 
        reviewer_topics = set(reviewer_topics)

        # submission topics := topics of submission
        # => used for removing words
        submission_topics = [ topic_id for topic_id, prob in enumerate(autobid.get_topics(submission.words)) if prob > 0 ]
        
        grid =  [ { 'op': 'add', 'no_words': config['step'], 'topic_id': topic_id, 'strategy_name': 'aggregated' } 
                    for topic_id in submission.strategies['aggregated'].create_topic_list(reviewer_topics) ]

        grid += [ { 'op': 'del', 'no_words': config['step'], 'topic_id': topic_id, 'strategy_name': 'aggregated' } 
                        for topic_id in submission.strategies['aggregated'].create_topic_list(submission_topics) ]

    elif config['strategy'] == 'word_based':

        grid = []
        for surrogate_idx, surrogate_model in enumerate(surrogate_models):
            no_reviewers = len(surrogate_model.reviewers_list)
            ranking = [ reviewer_name for reviewer_name, _ in surrogate_model.get_ranking(submission.words) ]
            
            for target_reviewer in chain(target['request'], target['reject']):

                target_reviewer_idx = surrogate_model.reviewers_list.index(target_reviewer)
                target_reviewer_rank = ranking.index(target_reviewer)
                
                if target_reviewer in target['request']:
                    # w = 3, offset = 1
                    #   * * * * *
                    # 0 1 2 3 4 5 6 7
                    #         ^
                    rank_high = min(target_reviewer_rank+config['reviewer_offset'], len(surrogate_model.reviewers_list))-1
                    rank_low = max(rank_high-config['reviewer_window'], 0)
                else:
                    # w = 3, offset = 1
                    #       * * * * *
                    # 0 1 2 3 4 5 6 7
                    #         ^
                    rank_low = max(target_reviewer_rank-config['reviewer_offset'], 0)
                    rank_high = min(target_reviewer_rank+config['reviewer_window'], len(surrogate_model.reviewers_list))-1                  

                reviewers = [ surrogate_model.reviewers_list.index(ranking[rank]) for rank in range(rank_low, rank_high+1) if rank != target_reviewer_rank]
                
                combs = [ comb for comb in chain.from_iterable(combinations(reviewers, r) for r in range(len(reviewers)+1)) ]
                
                for reviewer_idxes in combs:
                    mode = 'select' if target_reviewer in target['request'] else 'reject'
                    key = (surrogate_idx, target_reviewer_idx, reviewer_idxes, mode)
                    # init words
                    if len(submission.strategies['word_based'].init_words(key + ('add', ))) > 0:
                        grid += [ { 'op': 'add', 'no_words': config['step'], 'topic_id': key + ('add', ), 'strategy_name': 'word_based' } ]

                    if len(submission.strategies['word_based'].init_words(key + ('del', ))) > 0:
                        grid += [ { 'op': 'del', 'no_words': config['step'], 'topic_id': key + ('del', ), 'strategy_name': 'word_based' } ]

    else:
        topics_ids = list(range(grid_size))

        grid = [ { 'op': 'add', 'no_words': config['step'], 'topic_id': topic_id, 'strategy_name': config['strategy'] } 
                    for topic_id in topics_ids ]

        grid += [ { 'op': 'del', 'no_words': config['step'], 'topic_id': topic_id, 'strategy_name': config['strategy'] } 
                     for topic_id in topics_ids ] 

    k = min(len(grid), config['no_successors'])
    grid = random.sample(grid, k)

    return grid    