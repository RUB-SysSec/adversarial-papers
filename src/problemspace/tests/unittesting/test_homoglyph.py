from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.Transformer import Transformer
from problemspace.transformers.HomoglyphTransformer import HomoglyphTransformer
from problemspace.exceptions.TransformerException import TransformerException
from problemspace.tests.unittesting.UnitBaseClass import UnitBaseClass
from problemspace.transformers.TransformationState import TransformationState
from utils.pdf_utils import analyze_words


class TestHomoglyphTransformer(UnitBaseClass):

    def setUp(self):
        """
        Runs before any test.
        """
        self.setup_all()

    def test_hompglyph_transformer(self):
        wordsdict = {'hostil': -1, 'agtuexbuqjekk': -2}
        transf: Transformer = HomoglyphTransformer(logsettings = LogSettings(debug_coloring=False))
        self._test_homoglyph(wordsdict=wordsdict, transf=transf)

    def test_hompglyph_transformer2(self):
        wordsdict = {'hostil': -1, 'agtuexbuqjekk': -2}
        transf: Transformer = HomoglyphTransformer(logsettings = LogSettings(debug_coloring=True))
        self._test_homoglyph(wordsdict=wordsdict, transf=transf)

    def _test_homoglyph(self, wordsdict, transf):
        # the following transformer should only add kpqnfop4aatft 3x
        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)

        word_vector_after: list = analyze_words(
            pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        self.assertEqual(word_vector_after.count("hostil"), 1)  # hostil not possible, no suitable homoglyph!
        self.assertEqual(word_vector_after.count("agtuexbuqjekk"), 1)
        self.assertEqual(word_vector_after.count("kpqnfop4aatft"), 0)

        # check now that no other features were changed, these are the expected changes;
        expected_delta = {'agtueхbuqjekk': 1, 'agtuexьuqjekk': 1, 'agtuexbuqjekk': -2}
        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=expected_delta)


