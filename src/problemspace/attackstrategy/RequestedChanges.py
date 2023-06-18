from typing import Dict, Tuple, List
import copy
import logging

from utils.attack_utils import clean_dict, clean_discrepancies_find_words


class RequestedChanges:
    """
    Saves the requested changes from feature space for problem-space attack.
    """

    def __init__(self,
                 feature_space_results: Dict[str, list],
                 requested_changes_best: Dict[str, int],
                 logger: logging.Logger):

        self.feature_space_results = copy.deepcopy(feature_space_results)
        self.requested_changes_best = copy.deepcopy(requested_changes_best)

        self.removed_requested_changes_best: Dict[str, int] = {}
        self.removed_feature_space_results: Dict[str, List[Dict[str, int]]] = {}

        self.logger = logger

    def clean(self):
        self.requested_changes_best, self.removed_requested_changes_best = self.__clean(requested_changes=self.requested_changes_best)

        self.removed_feature_space_results['words_cnt'] = []
        for i in range(len(self.feature_space_results['words_cnt'])):
            req = self.feature_space_results['words_cnt'][i]
            req_cleaned, cleaned_feat = self.__clean(requested_changes=req)
            self.feature_space_results['words_cnt'][i] = req_cleaned
            self.removed_feature_space_results['words_cnt'].append(cleaned_feat)

    def __clean(self, requested_changes: Dict[str, int]) -> Tuple[Dict[str, int], Dict[str, int]]:

        r, c = clean_dict(requested_changes=requested_changes,
                   logger=self.logger,
                   max_ord_value=255)
        r2, c2 = clean_discrepancies_find_words(requested_changes=r)
        assert len(set(c).intersection(set(c2))) == 0
        c2.update(c)
        return r2, c2

