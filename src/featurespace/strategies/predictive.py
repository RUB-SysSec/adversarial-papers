
from collections import Counter, defaultdict
from utils.lda import get_topics_to_words
import numpy as np
from tqdm import tqdm

class PredictiveWordsStrategy:

    @staticmethod
    def is_ascii(word):
        return max(ord(c) for c in word) < 255

    def __init__(self, surrogate_models, config, features_blocked, n_sample_words=1000):
        self.words = defaultdict(dict)
        topics_to_words = get_topics_to_words(surrogate_models[0], config['lambda'], config['omega'])
        for topics in topics_to_words:
            words = self.sample_words(topics_to_words[topics], n_sample_words, features_blocked)
            if len(words) == 0:
                continue
            self.words[topics] = words

    def sample_words(self, words_probs, n_sample_words, features_blocked):
        words_probs = [ (word, prob) for word, prob in words_probs 
                                     if word not in features_blocked and PredictiveWordsStrategy.is_ascii(word) ]
        if len(words_probs) == 0:
            return []
        words, probs = zip(*words_probs)
        # normalize again to avoid numerical issues 
        probs = np.array(probs) / np.sum(probs)
        return [ word for word in np.random.choice(words, size=n_sample_words, p=probs)]

    def add_words(self, words_cnt, current_state, no_words, topic_combination):
        return words_cnt + Counter(self.words[topic_combination][current_state:current_state+no_words])

    def remove_words(self, words_cnt, current_state, no_words, topic_combination):
        words_to_remove = self.words[topic_combination][current_state:]
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
        topic_ids = set(topic_ids)
        topic_list = [ topics for topics in self.words.keys()
                              if set(topics).issubset(topic_ids) ]
        return topic_list
