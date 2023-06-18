import numpy as np

def loss(model, config, T, p):
    # calculate loss with raw scores
    scores = model.get_scores(p.words, normalized=False)
    ranks = { name : idx for idx, (name, _) in enumerate(sorted(zip(model.reviewers_list, scores),
                                                                    key=lambda x: x[1], reverse=True)) }

    # check if we are done
    requests_done = all([ (ranks[r] <  5) for r in T['request'] ]) if len(T['request']) > 0 else True
    rejects_done  = all([ (ranks[r] >= 5) for r in T['reject']  ]) if len(T['reject'])  > 0 else True
    finished = requests_done and rejects_done

    # loss
    loss = 0 
    if not finished:
        # requested reviewer
        for r in T['request']:
            t_index, _ = model.get_reviewer(r)
            s_tp = scores[t_index]
            loss += ranks[r] * (sorted(scores, reverse=True)[0] - s_tp) # 0 if reviewer is rank 1
        # rejected reviewer
        for r in T['reject']:
            r_index, _ = model.get_reviewer(r)
            s_rp = scores[r_index]
            loss += max(10 - ranks[r], 0) * (s_rp - sorted(scores, reverse=True)[9]) # 0 if reviewer is rank 10 or worse

    else:
        # normalize scores
        score_max = np.amax(scores)
        score_min = np.amin(scores)
        scores = (scores - score_min) / float(score_max - score_min)

        # we're done -> now maximize margin
        if len(T['request']) > 0:
            # distance from request to cutoff score
            min_score = min([ score for name, score in sorted(zip(model.reviewers_list, scores),
                                                        key=lambda x: x[1], reverse=True)[:5] 
                            if name in T['request'] ])
            request_distance = sorted(scores, reverse=True)[5] - min_score # rank 6 - min_score
        else:
            request_distance = None

        if len(T['reject']) > 0:
            # distance from reject to cutoff sccore
            max_score = max([ score for name, score in sorted(zip(model.reviewers_list, scores),
                                                        key=lambda x: x[1], reverse=True)[5:]
                            if name in T['reject'] ])
            reject_distance = max_score - sorted(scores, reverse=True)[4] # max_score - rank 5
        else:
            reject_distance = None
    
        if request_distance is None:
            loss = reject_distance
        elif reject_distance is None:
            loss = request_distance
        else:
            loss = max(request_distance, reject_distance)
    
    return loss
