import json
import numpy as np
from gensim.corpora import Dictionary
from sklearn.cluster import AgglomerativeClustering

def print_scores(logger, model, submission, target):
    logger.info("       Scores")
    ranking = model.get_ranking(submission.words)
    for idx, (reviewer_name, score) in enumerate(ranking[:10]):
        if reviewer_name in target['request']:
            status = "^"
        elif reviewer_name in target['reject']:
            status = "v"
        else:
            status = ""
        logger.info(f'       {idx+1:>2} {reviewer_name.upper().replace("_", " "):<20} ({model.reviewers_list.index(reviewer_name):>3}) : {score:.2f} {status}')
        if idx == 4:
            logger.info(f'        -')

def log_mem(prefix=""):        
    import resource
    mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1000
    print(f'    {prefix} @ Memory usage: {mb} (mb)')

def cluster(submissions, no_clusters):
    corpus = [ list(s.modified_words_cnt.keys()) for s in submissions ]
    dictionary = Dictionary(corpus)

    modified_words_vecs = []
    for s in submissions:
        modified_words_vec = np.zeros(len(dictionary))
        for word, cnt in s.modified_words_cnt.items():
            word_id =  dictionary.token2id[word] 
            modified_words_vec[word_id] = cnt
        modified_words_vecs += [ modified_words_vec ]

    model = AgglomerativeClustering(linkage="ward", affinity="euclidean", distance_threshold=None, n_clusters=no_clusters, compute_distances=True)    
    model.fit(modified_words_vecs)

    return model.labels_
