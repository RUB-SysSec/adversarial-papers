import pathlib

from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.Transformer import Transformer
from problemspace.transformers.bibtex.BibTexDatabase import BibTexDatabase
from problemspace.transformers.bibtex.FakeBibTexTransformer import FakeBibTexTransformer
from problemspace.tests.unittesting.UnitBaseClass import UnitBaseClass
from problemspace.transformers.TransformationState import TransformationState
from utils.pdf_utils import analyze_words


class TestFakeBibTexTransformer(UnitBaseClass):
    bibtexfiles = pathlib.Path.cwd().parent / "evaluation" / "bibsources"  # TODO unique config file for that

    def setUp(self):
        """
        Runs before any test.
        """
        self.setup_all()

        self.bibtexdatabase = BibTexDatabase(verbose=True)
        self.bibtexdatabase.load_bibtexdatabase_from_pickle(
            targetfilepath=self.bibtexfiles / "bibsources_bibtextests.pck")

    def _fakebibtex_common(self, wordsdict_example: dict):
        logsettings: LogSettings = LogSettings()
        transf: Transformer = FakeBibTexTransformer(bibtexdatabase=self.bibtexdatabase,
                                                    logsettings=logsettings, maxpapers=2, seed=42)

        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict_example)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)

        word_vector_after: list = analyze_words(
            pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        return word_vector_after

    def test_fakebibtex_transformer(self):
        wordsdict_example = {'cpu2022': 3, 'file': 3, 'atomic': 3, 'attack': 3,
                             'adversari': -4, 'wbx': 3, 'cch': 3, 'utf': 8}

        word_vector_after = self._fakebibtex_common(wordsdict_example=wordsdict_example)

        self.assertEqual(word_vector_after.count("cch"), 2)
        self.assertEqual(word_vector_after.count("utf"), 2)
        self.assertEqual(word_vector_after.count("cpu2022"), 0)

        # check now that no other features were changed
        ignore_addition_words_ = {'messeng': 1, 'encrypt': 1, 'papamanth': 1, 'catcher': 1, 'databas': 1, 'weippl': 1,
                                  'kornaropoulo': 1, 'secur': 1, 'data': 1, 'defens': 1, 'nearest': 1, 'research': 1,
                                  'ieee': 1, 'network': 1, 'oper': 1, 'recoveri': 1, 'intern': 1, 'petzl': 1,
                                  'dabrowski': 1, 'proc': 2, 'neighbor': 1, 'base': 1, 'intrus': 1, 'leakag': 1,
                                  'tamassia': 1, 'attack': 1, 'symposium': 2, 'raid': 1, 'page': 2, 'imsi': 1,
                                  'shoot': 1, 'privaci': 1, 'queri': 1, 'detect': 1,
                                  'wbx': 2, 'cch': 2, 'utf': 2}
        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=ignore_addition_words_)

    def test_fakebibtex_transformer2(self):
        wordsdict_example = {'cch': 1, 'attack': 3, 'adversari': 3}

        word_vector_after = self._fakebibtex_common(wordsdict_example=wordsdict_example)

        # check now that no other features were changed
        ignore_addition_words_ = {'gunter': 1, 'privaci': 1, 'ieee': 1, 'proc': 1, 'page': 1, 'symposium': 1,
                                  'effici': 1, 'safeti': 1, 'deploy': 1, 'winslett': 1, 'polici': 1, 'secur': 1,
                                  'firewal': 1, 'zhang': 1, 'wbx': 2, 'cch': 1, 'attack': 1, 'adversari': 1}
        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=ignore_addition_words_)
