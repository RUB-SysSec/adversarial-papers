from collections import Counter, OrderedDict

import numpy as np


class Submission:

    def __init__(self, strategies, words, initial_words):
        self.initial_words_cnt = Counter(initial_words)
        self.prior_modifications_cnt = Submission.get_modifications_cnt(Counter(initial_words), Counter(words))
        self.extra_words = []
        self.history = []
        self.strategies = strategies

    def __str__(self):
        deletions, additions = self.no_modified_words
        out = f"       {'Words':<16}: {len(self.initial_words)} +{additions} -{deletions} = {len(self.words)}"
        if len(self.history) > 0:
            last_op = self.history[-1]
            out += f"\n       {'Last':<16}: {last_op[0]} {last_op[3]} {last_op[1]} (topics {last_op[2]})"
        return out

    @staticmethod
    def get_modifications_cnt(initial, current):
        modified_words_cnt = current - initial     # added words
        modified_words_cnt_del = initial - current # deleted words
        for word, cnt in modified_words_cnt_del.items():
            modified_words_cnt[word] = -cnt
        modified_words_cnt = OrderedDict(modified_words_cnt.most_common())
        return modified_words_cnt

    @staticmethod
    def apply_modifications_cnt(initial, modifications):
        assert isinstance(initial, list) and isinstance(modifications, OrderedDict)
        words = initial
        for word, cnt in modifications.items():
            words += [word] * cnt
        return words
    
    @property
    def no_modified_words(self):
        initial = self.initial_words_cnt
        current = self.words_cnt
        added_words = sum([ cnt for cnt in (current - initial).values() ])
        deleted_words = sum([ cnt for cnt in (initial - current).values() ])
        return deleted_words, added_words
    
    @property
    def words(self):
        words = []
        for word, cnt in self.words_cnt.items():
            words += [word] * cnt
        return words

    @property
    def initial_words(self):
        words = []
        for word, cnt in self.initial_words_cnt.items():
            words += [word] * cnt
        return words
    
    @property
    def words_cnt(self):
        return self._words_cnt()

    def _words_cnt(self, skip_prior_modifiactions=False):
        states_add, states_del = {}, {}
        words_cnt = self.initial_words_cnt.copy()

        # add extra words
        for word in self.extra_words:
            words_cnt[word] += 1

        # apply prior modifications
        if not skip_prior_modifiactions:
            for word, cnt in self.prior_modifications_cnt.items():
                words_cnt[word] += cnt

        # init strategies states
        for strategy_name, strategy in self.strategies.items():
            states_add[strategy_name] = strategy.init_states()
            states_del[strategy_name] = strategy.init_states()

        # apply all operations from history
        for op, strategy_name, topic_id, no_words in self.history:
            if op == 'add':
                states_add[strategy_name][topic_id] += no_words
            else:
                states_del[strategy_name][topic_id] -= no_words

        # additions
        for strategy_name in self.strategies:
            for topic_id, no_words in states_add[strategy_name].items():
                strategy = self.strategies[strategy_name]
                words_cnt = strategy.add_words(words_cnt, 0, no_words, topic_id)

        # deletions
        for strategy_name in self.strategies:
            for topic_id, no_words in states_del[strategy_name].items():
                strategy = self.strategies[strategy_name]
                words_cnt = strategy.remove_words(words_cnt, 0, abs(no_words), topic_id)

        return words_cnt
    
    @property
    def modified_words_cnt(self):
        return self._modified_words_cnt()

    def _modified_words_cnt(self, skip_prior_modifiactions=False):
        words_cnt = self._words_cnt(skip_prior_modifiactions)
        return Submission.get_modifications_cnt(self.initial_words_cnt, words_cnt)

    def _modify(self, op, no_words, topic_id, strategy_name):
        new_submission = self.copy()
        if strategy_name not in new_submission.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        new_submission.history.append( (op, strategy_name, topic_id, no_words) )
        return new_submission

    def get_best_successors(self, grid, loss, n, max_inf_norm, max_man_norm):
        # avoid computing words_cnt from scratch for each candidate
        # => create new submission with current words
        cache_modified_words_cnt = self.modified_words_cnt
        cache = Submission(self.strategies, self.words, self.words)
        # create candidates 
        candidates = []
        for params in grid:
            candidate = cache._modify(**params)
            if max_inf_norm is not None:
                modified_words_cnt = Counter(cache_modified_words_cnt)
                for word, cnt in candidate.modified_words_cnt.items():
                    modified_words_cnt[word] += cnt
                inf_norm = max( [ abs(cnt) for cnt in modified_words_cnt.values() ] + [0] )
                if inf_norm > max_inf_norm:
                    continue
            if max_man_norm is not None:
                modified_words_cnt = Counter(cache_modified_words_cnt)
                for word, cnt in candidate.modified_words_cnt.items():
                    modified_words_cnt[word] += cnt
                man_norm = sum( [ abs(cnt) for cnt in modified_words_cnt.values() ] )
                if man_norm > max_man_norm:
                    continue                      
            candidates += [ (params, loss(candidate)) ]
        # select n best successors
        candidates = sorted(candidates, key=lambda x: x[1], reverse=False)
        successors = []
        for idx in range(min(n, len(candidates))):
            candidate_params, _ = candidates[idx]
            successors += [ self._modify(**candidate_params) ]
        return successors

    def copy(self):
        words = Submission.apply_modifications_cnt(self.initial_words, self.prior_modifications_cnt)
        submission = Submission(self.strategies, words, self.initial_words)
        submission.history = self.history.copy()
        return submission

    @property
    def linf(self):
        if len(self.modified_words_cnt) == 0:
            return 0
        return np.linalg.norm(list(self.modified_words_cnt.values()), np.inf)
    
    @property
    def l1(self):
        return np.linalg.norm(list(self.modified_words_cnt.values()), 1)

    OP_TO_ID = {}
    @property
    def history_ids(self):
        op_ids = []
        for op in self.history:
            if op not in Submission.OP_TO_ID:
                 Submission.OP_TO_ID[op] = f'{len(Submission.OP_TO_ID):0>3x}'
            op_id = Submission.OP_TO_ID[op]
            op_ids += [op_id]
        return " ".join(sorted(op_ids))