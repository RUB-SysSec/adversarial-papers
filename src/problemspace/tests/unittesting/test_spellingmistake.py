from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.Transformer import Transformer
from problemspace.transformers.spellingmistakes.SpellingMistakeTransformer import SpellingMistakeTransformer, \
    SpellingMistakeTransformerOption
from problemspace.tests.unittesting.UnitBaseClass import UnitBaseClass
from problemspace.transformers.TransformationState import TransformationState
from utils.pdf_utils import analyze_words


class TestSpellingMistakeTransformer(UnitBaseClass):
    # stem "consider" comes from "considerable" (note that stem of consider is consid!)
    # stem "secur" comes from "security".
    # We test here each TransfomerOption {swap_letters, delete_letter, random_swap_delete, common_typos}
    # * Debug-Coloring {yes, no} = 8 tests.

    def setUp(self):
        """
        Runs before any test.
        """
        self.setup_all()

    def test_spellingmistake_transformer1(self):
        wordsdict = {'hostil': -1, 'consider': -2, 'secur': -3, 'agtuexbuqjekk': -1}
        expected_delta = {'seucriti': 3, 'consdier': 1, 'agtuxebuqjekk': 1,
                          'consider': -1, 'secur': -3, 'agtuexbuqjekk': -1}
        transf: Transformer = SpellingMistakeTransformer(logsettings = LogSettings(debug_coloring=True),
                                                         transformeroption=SpellingMistakeTransformerOption.SWAP_LETTERS)
        self._test_spellingmistake(wordsdict=wordsdict, transf=transf, expected_delta=expected_delta)

    def test_spellingmistake_transformer1b(self):
        wordsdict = {'hostil': -1, 'consider': -2, 'secur': -3, 'agtuexbuqjekk': -1}
        expected_delta = {'seucriti': 3, 'consdier': 1, 'agtuxebuqjekk': 1,
                          'consider': -1, 'secur': -3, 'agtuexbuqjekk': -1}
        transf: Transformer = SpellingMistakeTransformer(logsettings = LogSettings(debug_coloring=False),
                                                         transformeroption=SpellingMistakeTransformerOption.SWAP_LETTERS)
        self._test_spellingmistake(wordsdict=wordsdict, transf=transf, expected_delta=expected_delta)


    def test_spellingmistake_transformer2(self):
        wordsdict = {'hostil': -1, 'consider': -2, 'secur': -3, 'agtuexbuqjekk': -1}
        expected_delta = {'secuiti': 2, 'seuriti': 1, 'cosider': 1, 'agtexbuqjekk': 1,
                          'consider': -1, 'secur': -3, 'agtuexbuqjekk': -1}
        transf: Transformer = SpellingMistakeTransformer(logsettings = LogSettings(debug_coloring=True),
                                                         transformeroption=SpellingMistakeTransformerOption.DELETE_LETTER)
        self._test_spellingmistake(wordsdict=wordsdict, transf=transf, expected_delta=expected_delta)

    def test_spellingmistake_transformer2b(self):
        wordsdict = {'hostil': -1, 'consider': -2, 'secur': -3, 'agtuexbuqjekk': -1}
        expected_delta = {'secuiti': 2, 'seuriti': 1, 'cosider': 1, 'agtexbuqjekk': 1,
                          'consider': -1, 'secur': -3, 'agtuexbuqjekk': -1}
        transf: Transformer = SpellingMistakeTransformer(logsettings = LogSettings(debug_coloring=False),
                                                         transformeroption=SpellingMistakeTransformerOption.DELETE_LETTER)
        self._test_spellingmistake(wordsdict=wordsdict, transf=transf, expected_delta=expected_delta)


    def test_spellingmistake_transformer3(self):
        wordsdict = {'hostil': -1, 'consider': -2, 'secur': -3}
        expected_delta = {'consdier': 1, 'seuriti': 1, 'seucriti': 2,
                          'consider': -1, 'secur': -3}
        transf: Transformer = SpellingMistakeTransformer(logsettings = LogSettings(debug_coloring=True),
                                                         transformeroption=SpellingMistakeTransformerOption.SWAP_OR_DELETE_RANDOMLY)
        self._test_spellingmistake(wordsdict=wordsdict, transf=transf, expected_delta=expected_delta)

    def test_spellingmistake_transformer3b(self):
        wordsdict = {'hostil': -1, 'consider': -2, 'secur': -3}
        expected_delta = {'consdier': 1, 'seuriti': 1, 'seucriti': 2,
                          'consider': -1, 'secur': -3}
        transf: Transformer = SpellingMistakeTransformer(logsettings = LogSettings(debug_coloring=False),
                                                         transformeroption=SpellingMistakeTransformerOption.SWAP_OR_DELETE_RANDOMLY)
        self._test_spellingmistake(wordsdict=wordsdict, transf=transf, expected_delta=expected_delta)

    def test_spellingmistake_transformer4(self):
        wordsdict = {'hostil': -1, 'consider': -2, 'secur': -3, 'agtuexbuqjekk': -1}
        expected_delta = {'secuer': 2, 'considr': 1, 'scuriti': 1, 'agtuxbuqjkk': 1,
                          'consider': -1, 'secur': -3, 'agtuexbuqjekk': -1}
        transf: Transformer = SpellingMistakeTransformer(logsettings = LogSettings(debug_coloring=True),
                                                         transformeroption=SpellingMistakeTransformerOption.COMMON_TYPOS)
        self._test_spellingmistake(wordsdict=wordsdict, transf=transf, expected_delta=expected_delta)

    def test_spellingmistake_transformer4b(self):
        wordsdict = {'hostil': -1, 'consider': -2, 'secur': -3, 'agtuexbuqjekk': -1}
        expected_delta = {'secuer': 2, 'considr': 1, 'scuriti': 1, 'agtuxbuqjkk': 1,
                          'consider': -1, 'secur': -3, 'agtuexbuqjekk': -1}
        transf: Transformer = SpellingMistakeTransformer(logsettings = LogSettings(debug_coloring=False),
                                                         transformeroption=SpellingMistakeTransformerOption.COMMON_TYPOS)
        self._test_spellingmistake(wordsdict=wordsdict, transf=transf, expected_delta=expected_delta)

    def test_spellingmistake_transformer5(self):
        wordsdict = {'program': -1, 'consider': -2} # program has no "common_typo".
        expected_delta = {'considr': 1, 'prgoram': 1, 'program': -1, 'consider': -1}
        transf: Transformer = SpellingMistakeTransformer(logsettings = LogSettings(debug_coloring=False),
                                                         transformeroption=SpellingMistakeTransformerOption.COMMON_TYPOS_OTHERWISE_TRY_RANDOMLY_SWAP_DELETE)
        self._test_spellingmistake(wordsdict=wordsdict, transf=transf, expected_delta=expected_delta)

    def test_spellingmistake_transformer6Max(self):
        # Lets test if we can set the maximum number of changes correctly
        wordsdict = {'hostil': -1, 'consider': -2, 'secur': -3, 'program': -1}
        expected_delta = {'scuriti': 1, 'considr': 1, 'consider': -1, 'secur': -1}
        transf: Transformer = SpellingMistakeTransformer(max_changes=2,
                                                         logsettings=LogSettings(debug_coloring=False),
                                                         transformeroption=SpellingMistakeTransformerOption.COMMON_TYPOS_OTHERWISE_TRY_RANDOMLY_SWAP_DELETE)
        self._test_spellingmistake(wordsdict=wordsdict, transf=transf, expected_delta=expected_delta)

    def _test_spellingmistake(self, wordsdict, transf, expected_delta):
        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)

        word_vector_after: list = analyze_words(
            pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        self.assertEqual(word_vector_after.count("hostil"), 1)  # hostil not possible

        # check now that no other features were changed, these are the expected changes;
        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=expected_delta)

        # Check that no side effects are present except for adding new words:
        self.assertEqual(sum(newtransfstate.side_effects_worddict.values()), sum([v for v in expected_delta.values() if v > 0]))
