
from collections import Counter, defaultdict
import numpy as np
import json
from itertools import chain


class WordStrategy:

    def __init__(self, surrogate_models, target, features_blocked, submission_words, n_sample_words=1000):

        self.words = {}
        self.features_blocked = features_blocked
        self.n_sample_words = n_sample_words
        # assert len(target['request']) <= 1 and len(target['reject']) <= 1

        self.surrogate_to_reviewers_words = [ [dict(reviewer_words) for reviewer_words in json.loads(surrogate_model.model_dir.joinpath('reviewer_to_words_mapping.json').read_text()) ]
                                               for surrogate_model in surrogate_models                                                      ]
        self.submission_words = submission_words

    def init_words(self, key):

        # is cached?
        if key in self.words:
            return self.words[key]
        
        surrogate_idx, target_reviewer_idx, reviewer_idxes, mode, op = key
        reviewers_words = self.surrogate_to_reviewers_words[surrogate_idx]
        target_reviewer_words = reviewers_words[target_reviewer_idx]

        # get words
        if len(reviewer_idxes) == 0:
            words = set(target_reviewer_words)

        elif (mode == 'select' and op == 'add') or (mode == 'reject' and op == 'del'):
            # words that predictive for target but not surrounding
            # -> add to promote target
            # -> del to demote targettarget
            words = set(target_reviewer_words) - set.union(*[set(reviewers_words[reviewer_idx]) for reviewer_idx in reviewer_idxes ])

        elif (mode == 'select' and op == 'del') or (mode == 'reject' and op == 'add'):
            # words that predictive for surrounding but not target
            # -> del to promote target
            # -> add to demote target            
            words = set.intersection(*[set(reviewers_words[reviewer_idx]) for reviewer_idx in reviewer_idxes ]) - set(target_reviewer_words)

        else:
            raise ValueError(key)

        if op == 'del':
            words = [ word for word in words if word in self.submission_words ]

        # filter words
        words = [  word for word in words if word not in self.features_blocked ]

        # get probs
        if len(words) == 0:
            words = []
        else:
            if (mode == 'select' and op == 'add') or (mode == 'reject' and op == 'del') or len(reviewer_idxes) == 0:
                probs = [ target_reviewer_words[word] for word in words ]
            else:
                probs = [ np.mean([reviewers_words[reviewer_idx][word] for reviewer_idx in reviewer_idxes]) for word in words]
                
            probs = np.array(probs) / np.sum(probs)
            words = [ word for word in np.random.choice(words, self.n_sample_words, p=probs) ]
        self.words[key] = words

        return self.words[key]

    def add_words(self, words_cnt, current_state, no_words, topic_id):
        return words_cnt + Counter(self.words[topic_id][current_state:current_state+no_words])

    def remove_words(self, words_cnt, current_state, no_words, topic_id):
        words_to_remove = self.words[topic_id][current_state:]
        cnt = 0
        for word in words_to_remove:
            # are we done?
            if cnt == no_words:
                break
            # try to find word
            if words_cnt[word] >= 1:
                words_cnt[word] -= 1
                cnt += 1
        return words_cnt

    def init_states(self):
        update_idxes = defaultdict(lambda: 0)
        return update_idxes

    def create_topic_list(self, topic_ids):
        topic_list = [ topic_id for topic_id in self.words 
                                if topic_id in topic_ids ]
        return topic_list
