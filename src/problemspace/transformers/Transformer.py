import sys
import typing
import pathlib
import string
import random
import logging
import traceback
import collections
from abc import ABC, abstractmethod
import pickle

from problemspace.transformers.LogSettings import LogSettings
from problemspace.exceptions.PdfLatexException import PdfLatexException
from problemspace.PdfLatexSource import PdfLatexSource
from problemspace.exceptions.TransformerException import TransformerException
from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.FeatureDelta import FeatureDelta
from utils.pdf_utils import analyze_words


class Transformer(ABC):
    """
    Generic transformer to change a latex-pdf file.
    """

    def __init__(self, logsettings: LogSettings):
        """
        Init Transformer
        :param logsettings: Log Settings
        """

        self.debug_coloring: bool = logsettings.debug_coloring
        self.logger: typing.Optional[logging.Logger] = logsettings.logger
        self.error_dir: pathlib.Path = logsettings.error_dir

    def apply_transformer(self, transformationstate: TransformationState) -> TransformationState:
        """
        :param transformationstate: pdf latex document on disk, dict with wanted changes...
        :return a new transformation state
        """

        # 1. copy source
        newtransformationstate: TransformationState = transformationstate.copyto()

        # 2. execute transformer, check if worked
        try:
            featdelta: FeatureDelta = self._transform(transformationstate=newtransformationstate)

            if len(featdelta.changes) != 0:
                newtransformationstate.pdflatexsource.runpdflatex()
                self.extract_side_effects(featuredelta=featdelta,
                                          transformationstate_before=transformationstate,
                                          transformationstate_after=newtransformationstate)
                self.update_wordsdict(transformationstate=newtransformationstate, featuredelta=featdelta)
                self.update_problemspacerestrictions(transformationstate=newtransformationstate,
                                                  featuredelta=featdelta)

                newtransformationstate.update_applied_transformers(applied_transformer=self.__class__.__name__)
                return newtransformationstate
            else:
                self.printlogdebug(f"                -> Transformer {self.__class__.__name__} not used.")
                return transformationstate

        except (TransformerException, PdfLatexException) as e:
            self.printlogerr("        -> ProblemSpace: Error for transformer: {}".format(str(e)))
            self.printlogerr(traceback.format_exc())
            self.saveerror(new_transformationstate=newtransformationstate, prev_transformationstate=transformationstate)
            return transformationstate
        except Exception as e:
            self.printlogerr("        -> ProblemSpace: Severe Error for transformer: {}".format(str(e)))
            self.printlogerr(traceback.format_exc())
            self.saveerror(new_transformationstate=newtransformationstate, prev_transformationstate=transformationstate)
            return transformationstate

    @abstractmethod
    def _transform(self, transformationstate: TransformationState) -> FeatureDelta:
        pass

    def extract_side_effects(self,
                             featuredelta: FeatureDelta,
                             transformationstate_before: TransformationState,
                             transformationstate_after: TransformationState) -> None:
        changed_features: FeatureDelta = FeatureDelta()

        pdffile_before: pathlib.Path = transformationstate_before.pdflatexsource.get_maindocument_tempfile(suffix="pdf")
        if not pdffile_before.exists():
            self.printlogdebug(
                "    -> ProblemSpace: Extract side effects: I need to run pdflatex for pdf file (Unusual behaviour)")
            transformationstate_before.pdflatexsource.runpdflatex()
            assert pdffile_before.exists()

        pdffile_after: pathlib.Path = transformationstate_after.pdflatexsource.get_maindocument_tempfile(suffix="pdf")
        assert pdffile_after.exists()  # should be true, since we run it in apply_transformer!

        word_vector_before: typing.List[str] = analyze_words(pdf_file=pdffile_before)
        word_vector_after: typing.List[str] = analyze_words(pdf_file=pdffile_after)

        word_vector_before_counter = collections.Counter(word_vector_before)
        word_vector_after_counter = collections.Counter(word_vector_after)

        all_keys = set().union(word_vector_before_counter.keys(), word_vector_after_counter.keys())
        for curkey in all_keys:
            # we use that if curkey is not present in counter, value is 0 automatically.
            if curkey in featuredelta.changes:
                if word_vector_after_counter[curkey] != (word_vector_before_counter[curkey] + featuredelta[curkey]):
                    changed_features[curkey] = word_vector_after_counter[curkey] - \
                                               (word_vector_before_counter[curkey] + featuredelta[curkey])
            else:
                if word_vector_after_counter[curkey] != word_vector_before_counter[curkey]:
                    changed_features[curkey] = word_vector_after_counter[curkey] - word_vector_before_counter[curkey]

        transformationstate_after.update_side_effects_with_delta(deltadict=changed_features,
                                                                 applied_transformer=self.__class__.__name__)

    def update_wordsdict(self, transformationstate: TransformationState, featuredelta: FeatureDelta):
        transformationstate.update_with_delta(deltadict=featuredelta,
                                              applied_transformer=self.__class__.__name__)

    def update_problemspacerestrictions(self, transformationstate: TransformationState, featuredelta: FeatureDelta):
        transformationstate.update_problemspacerestrictions(deltadict=featuredelta)

    def printlogerr(self, msg: str) -> None:
        if self.logger is not None:
            self.logger.error(msg)
        else:
            print(msg, file=sys.stderr)

    def printlogdebug(self, msg: str) -> None:
        if self.logger is not None:
            self.logger.debug(msg)
        else:
            print(msg)

    def saveerror(self,
                  prev_transformationstate: TransformationState,
                  new_transformationstate: TransformationState) -> None:
        """
        If error dir is given, this function will save the latex project with error to error dir.
        In this way, we can debug errors more easily.
        :param prev_transformationstate: previous transformation state without error.
        :param new_transformationstate: new transformation state with error.
        """
        if self.error_dir is not None:
            random_dir_name = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
            final_error_dir: pathlib.Path = self.error_dir / random_dir_name

            new_transformationstate.pdflatexsource.copy_project_for_debugging(targetdir=final_error_dir / "new")
            prev_transformationstate.pdflatexsource.copy_project_for_debugging(targetdir=final_error_dir / "prev")

            with open(final_error_dir / "new_transformationstate.pck", 'wb') as handle:
                pickle.dump(new_transformationstate, handle)
            with open(final_error_dir / "prev_transformationstate.pck", 'wb') as handle:
                pickle.dump(prev_transformationstate, handle)

            self.printlogerr(
                "        -> ProblemSpace: Whole project is saved for debugging to: {}".format(str(final_error_dir)))

    def saveerrorlatexsource(self, pdflatexsource: PdfLatexSource) -> None:
        """
        If error dir is given, this function will save the latex project with error to error dir.
        In this way, we can debug errors more easily.
        :param pdflatexsource: pdflatexsource
        """
        if self.error_dir is not None:
            random_dir_name = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
            final_error_dir: pathlib.Path = self.error_dir / random_dir_name
            pdflatexsource.copy_project_for_debugging(targetdir=final_error_dir)
            self.printlogerr(
                "        -> ProblemSpace: Latex Project with error is saved to: {}".format(str(final_error_dir)))
