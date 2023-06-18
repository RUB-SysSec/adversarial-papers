from typing import Dict, Optional, Tuple
import logging
import copy
import utils.pdf_utils


def clean_dict(requested_changes: Dict[str, int],
               logger: Optional[logging.Logger],
               max_ord_value: int) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Removes words that could cause latex compilation errors
    :param requested_changes: dictionary that contains the requested words to be added/removed/changed
    :param logger: logging, optional
    :param max_ord_value: max ord value of any character in word
    :return: requested changes, removed features
    """
    requested_changes = copy.deepcopy(requested_changes)

    def max_ord(s):
        return max(ord(c) for c in s)

    unvalid_features = {}
    for requested_word in list(requested_changes.keys()):
        if max_ord(requested_word) > max_ord_value:
            # if logger is not None:
            #     logger.info(f"Word-Deletion: {requested_word}, {requested_changes[requested_word]}")
            unvalid_features[requested_word] = requested_changes[requested_word]
            del requested_changes[requested_word]

    return requested_changes, unvalid_features

def clean_text(input_text: str,
               logger: Optional[logging.Logger],
               max_ord_value: int) -> str:
    """
    Removes characters in input text that could cause latex compilation errors
    :param input_text: text to be cleaned
    :param logger: logging, optional
    :param max_ord_value: max ord value of any character in word
    :return: cleaned text
    """
    problem_chars = []
    for c in input_text:
        if ord(c) > max_ord_value:
            if logger is not None:
                logger.debug(f"Char-Deletion: {input_text}, {c}")
            problem_chars.append(c)

    for c in problem_chars:
        input_text = input_text.replace(c, "")

    return input_text

def clean_discrepancies_find_words(requested_changes: Dict[str, int]) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Clean words that will be removed later in the text preprocessing phase.
    """
    requested_changes = copy.deepcopy(requested_changes)
    unvalid_features = {}
    for requested_word in list(requested_changes.keys()):
        if utils.pdf_utils.is_digit(requested_word) or len(requested_word) <= 1:  # Reject numbers and single letters
            unvalid_features[requested_word] = requested_changes[requested_word]
            del requested_changes[requested_word]

    return requested_changes, unvalid_features

def add_words_padding(requested_word: str, stemmer, logger: logging.Logger) -> Optional[str]:
    """
    For example, we have a problem if stem of stemmed word is again different
    e.g., stem(disproportionate) => stem(disproportion) => stem(disproport)
    To avoid this, we add another stem.
    """

    # we may have a problem if stem of stemmed word is again different
    # e.g., stem(disproportionate) => stem(disproportion) => stem(disproport)
    if stemmer.stem(requested_word) == requested_word:
        return requested_word
    else:
        # we iterate over multiple stems that could help
        for padded_stem in ["ate", "ed", "able", "es"]:
            ks = requested_word + padded_stem
            if stemmer.stem(ks) == requested_word:
                # logger.debug(f"        -> ProblemSpace: Stemming Issue {stemmer.stem(requested_word)} vs. {requested_word} solved with padded stem {padded_stem}.")
                return ks

        logger.debug(f"        -> ProblemSpace: Stemming Issue {stemmer.stem(requested_word)} vs. {requested_word} not solved with padded stems (ate, ed, able).")
        return None

def add_words_stop_words_padding(requested_word: str, stemmer, logger: logging.Logger) -> Optional[str]:
    """
    It can happen that a requested word is a stop word. Here, we add something, so that
    it is not recognized anymore as stop-word, but becomes the requested word after stemming.
    """
    stop_words: set = utils.pdf_utils.get_stop_words()
    if requested_word not in stop_words:
        return requested_word
    else:
        for padded_stem in ["ate", "ed", "able", "es"]:
            ks = requested_word + padded_stem
            if ks not in stop_words and stemmer.stem(ks) == requested_word:
                # logger.debug(f"        -> ProblemSpace: Stop-Word Issue {requested_word} solved with padded stem {padded_stem}.")
                return ks

        logger.debug(f"        -> ProblemSpace: Stop-Word Issue {requested_word} not solved with padded stems (ate, ed, able).")
        return None


