import typing
import copy

from problemspace.PdfLatexSource import PdfLatexSource
from problemspace.exceptions.TransformerException import TransformerException
from problemspace.transformers.FeatureDelta import FeatureDelta


class TransformationState:
    """
    Keeps tracks of transformations.
    It saves the PDF-Latex document, the original words/features to be added/removed,
    the currently achieved added/removed words/features (=delta between should-be and currently-is).
    """

    def __init__(self, pdflatexsource: PdfLatexSource,
                 original_wordsdict: typing.Optional[typing.Dict[str, int]] = None,
                 current_wordsdict: typing.Optional[typing.Dict[str, int]] = None,
                 side_effects_worddict: typing.Optional[typing.Dict[str, int]] = None,
                 applied_transformers: typing.Optional[typing.List[str]] = None,
                 probspacerestrictions: typing.Optional[typing.Set[str]] = None
                 ):
        """
        Inits a tranformation state.
        :param pdflatexsource: pdf latex object
        :param original_wordsdict: original dictionary with features that need to be changed
        :param current_wordsdict: the currently achieved changes (can be None if this is the start
        transformation state, in this case, current_words is set to a copy of original_wordsdict.
        :param side_effects_worddict: the currently observed side effects due to changes.
        :param applied_transformers: list of applied transformers so far.
        :param probspacerestrictions: words that should be blocked (problem-space constraints)
        """
        self.pdflatexsource: PdfLatexSource = pdflatexsource
        self.original_wordsdict: typing.Dict[str, int] = original_wordsdict

        self.current_wordsdict: typing.Dict[str, int] = current_wordsdict if \
            current_wordsdict is not None else copy.deepcopy(original_wordsdict)
        self.side_effects_worddict: typing.Dict[str, int] = side_effects_worddict if \
            side_effects_worddict is not None else {}

        self.applied_transformers: typing.List[str] = applied_transformers if \
            applied_transformers is not None else []
        self.probspacerestrictions: typing.Set[str] = probspacerestrictions if \
            probspacerestrictions is not None else set()

        self.history_group: str = "0"
        self.history: typing.Dict[str, typing.List[typing.Tuple[str, typing.Dict]]] = {}
        self.history_side_effects: typing.Dict[str, typing.List[typing.Tuple[str, typing.Dict]]] = {}

    def update_target_wordsdict(self, wordsdict: typing.Dict[str, int]) -> None:
        """
        We can overwrite the target dictionary if we get new
        information, e.g. from the feature space which
        words should be changed.
        In other words, we update our target vector.
        :param wordsdict: new words-dictionary
        """
        self.current_wordsdict = copy.deepcopy(wordsdict)
        self.original_wordsdict = wordsdict

    def extend_wordsdict(self, wordsdict: typing.Dict[str, int]):
        for k, v in wordsdict.items():
            if k in self.current_wordsdict:
                self.current_wordsdict[k] += v  # '+' because we add more words with pos/neg score.
            else:
                self.current_wordsdict[k] = v

    def update_with_delta(self, deltadict: FeatureDelta, applied_transformer: str):
        self._save_history_information(hist=self.history, deltadict=deltadict,
                                       applied_transformer=applied_transformer)
        for k, v in deltadict.changes.items():
            if k not in self.current_wordsdict:
                raise TransformerException("Word in delta is not present in saved words-dict")
            self.current_wordsdict[k] -= v  # '-' because we want to decrease count for words that were added/removed

    def get_delta(self):
        delta_dict: typing.Dict[str, int] = {}
        for k, v in self.current_wordsdict.items():
            if k not in self.original_wordsdict:
                raise TransformerException("Severe Error: Mismatch in key in original_wordsdict and current_wordsdict")
            delta_dict[k] = self.current_wordsdict[k] - self.original_wordsdict[k]
        return delta_dict

    def update_side_effects_with_delta(self, deltadict: FeatureDelta, applied_transformer: str):
        self._save_history_information(hist=self.history_side_effects, deltadict=deltadict,
                                       applied_transformer=applied_transformer)
        for k, v in deltadict.changes.items():
            if k not in self.side_effects_worddict:
                self.side_effects_worddict[k] = v
            else:
                self.side_effects_worddict[k] += v  # '+' because we update words with pos/neg score.

    def _save_history_information(self, hist: typing.Dict[str, typing.List[typing.Tuple[str, typing.Dict]]],
                                  deltadict: FeatureDelta,
                                  applied_transformer: str):
        """
        Helper fct. to save information that are useful for debugging later.
        Here, we save which transformer at which point changed which features.
        """
        if self.history_group not in hist:
            hist[self.history_group] = []
        hist[self.history_group].append((applied_transformer, deltadict.get_json_dump_output()))

    def update_applied_transformers(self, applied_transformer: str) -> None:
        self.applied_transformers.append(applied_transformer)

    def update_problemspacerestrictions(self, deltadict: FeatureDelta) -> None:
        self.probspacerestrictions.update(deltadict.unrealizable_words)

    def copyto(self) -> 'TransformationState':
        pds = self.pdflatexsource.copyto()
        ow = copy.deepcopy(self.original_wordsdict)
        cw = copy.deepcopy(self.current_wordsdict)
        se = copy.deepcopy(self.side_effects_worddict)
        ap = copy.deepcopy(self.applied_transformers)
        ac = copy.deepcopy(self.probspacerestrictions)
        tr = TransformationState(pdflatexsource=pds, current_wordsdict=cw,
                                 original_wordsdict=ow, side_effects_worddict=se,
                                 applied_transformers=ap, probspacerestrictions=ac)
        tr.history = copy.deepcopy(self.history)
        tr.history_side_effects = copy.deepcopy(self.history_side_effects)
        return tr

