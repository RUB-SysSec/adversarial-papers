
from collections import Counter, defaultdict
import numpy as np

class BasicStrategy:

    def __init__(self, autobid, n_sample_words=5000):
        self.words = {}
        for topic_id in range(autobid.no_topics):
            words, probs = zip(*[ (autobid.model.id2word.id2token[token_id], prob) 
                                   for token_id, prob in autobid.model.get_topic_terms(topic_id, int(1e6))
                                   if prob > 1e-8 ])
            probs = np.array(probs) / np.sum(probs)
            self.words[topic_id] = np.random.choice(words, n_sample_words, p=probs)

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
