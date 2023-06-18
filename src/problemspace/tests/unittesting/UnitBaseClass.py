import unittest
import pathlib
import collections
import typing
import sys

from problemspace.PdfLatexSource import PdfLatexSource
from utils.pdf_utils import analyze_words


class UnitBaseClass(unittest.TestCase):
    """
    Input-output testing. We check that the transformers create the expected behaviour after the transformation.
    The inner parts are not tested, yet.
    """

    def setup_all(self, default_latex_project: str = "unit_latex") -> None:
        """
        Should be called before any test is started. You should call this method from setUp().
        This method loads a respective pdf-latex file, parses it, and checks some features, so that
        we can run and test our transformers.
        :param default_latex_project: directory of latex project that is used for tests. Default is "unit_latex".
        """
        # super().__init__()

        # 1) Set up latex file and corresponding python object, extract features
        path_to_latex_file: pathlib.Path = pathlib.Path.cwd() / "problemspace" / "tests" / "unittesting" / default_latex_project
        self.problemspace_path: pathlib.Path = pathlib.Path.cwd() / "problemspace"

        pdflatexsource: PdfLatexSource = PdfLatexSource(latexsourcedir=path_to_latex_file, latexmainfilename="main.tex")

        # avoid messing up original directory, let's copy pdf file to a new temporary directory in /tmp
        self.newpdflatexsource: PdfLatexSource = pdflatexsource.copyto()
        self.newpdflatexsource.runpdflatex()

        # get file path to pdf of main document
        self.pdfile_ = self.newpdflatexsource.get_maindocument_tempfile(suffix="pdf")
        # extract features
        self.word_vector_before: list = analyze_words(pdf_file=self.pdfile_)

        # 2) Check that features that are either removed or added have the correct initial value
        if default_latex_project == "unit_latex":
            # 2.a) Features that can be removed
            self.assertEqual(self.word_vector_before.count("hostil"), 1)
            # Choose a random string that added before. This string is present at the beginning of the 'Background' section.
            self.assertEqual(self.word_vector_before.count("agtuexbuqjekk"), 3)

            # 2.b) Features that we can add
            self.assertEqual(self.word_vector_before.count("kpqnfop4aatft"), 0) # choose a random string

        elif default_latex_project == "unit_latex_2":
            pass # no tests yet for unit_latex_2


    @staticmethod
    def check_counts_before_and_after_valuebased(word_vector_before: typing.List[str],
                                      word_vector_after: typing.List[str],
                                      ignore_words: typing.Dict[str, int]):

        word_vector_before_counter = collections.Counter(word_vector_before)
        word_vector_after_counter = collections.Counter(word_vector_after)

        for k, v in word_vector_after_counter.items():
            if v != (word_vector_before_counter[k] + ignore_words.get(k, 0)):
                print(f"Comparison error for word: {k}; values mismatch: {v} != "
                      f"({word_vector_before_counter[k]} + {ignore_words.get(k, 0)})",
                          file=sys.stderr)
                raise ValueError()

        for k, v in word_vector_before_counter.items():
            if v != (word_vector_after_counter[k] - ignore_words.get(k, 0)):
                print(f"Comparison error for word: {k}; values mismatch: {v} != "
                      f"({word_vector_after_counter[k]} - {ignore_words.get(k, 0)})",
                          file=sys.stderr)
                raise ValueError()

