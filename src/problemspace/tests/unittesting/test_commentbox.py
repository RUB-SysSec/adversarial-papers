from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.Transformer import Transformer
from problemspace.transformers.CommentBoxAddWordTransformer  import CommentBoxAddWordTransformer
from problemspace.transformers.CommentBoxDelWordTransformer  import CommentBoxDelWordTransformer
from problemspace.tests.unittesting.UnitBaseClass import UnitBaseClass
from problemspace.transformers.TransformationState import TransformationState
from utils.pdf_utils import analyze_words


class TestCommentBoxTransformer(UnitBaseClass):

    def setUp(self):
        """
        Runs before any test.
        """
        self.setup_all()


    def test_commentbox_transformer(self):
        wordsdict = {'kpqnfop4aatft': 3, 'hostil': -1, 'agtuexbuqjekk': -3}

        transf: Transformer = CommentBoxAddWordTransformer(logsettings = LogSettings(debug_coloring=True))
        # the following transformer should only add kpqnfop4aatft 3x
        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)

        word_vector_after: list = analyze_words(pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        self.assertEqual(1, word_vector_after.count("hostil"))
        self.assertEqual(2, word_vector_after.count("agtuexbuqjekk"))
        self.assertEqual(3, word_vector_after.count("kpqnfop4aatft"))

        # check now that no other features were changed
        expected_delta = {'kpqnfop4aatft': 3, 'agtuexbuqjekk': -1}
        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=expected_delta)

        self.assertEqual(len(newtransfstate.side_effects_worddict), 0)


    def test_commentbox_transformer_just_addition(self):
        wordsdict = {'kpqnfop4aatft': 3}

        transf: Transformer = CommentBoxAddWordTransformer(logsettings = LogSettings(debug_coloring=True))
        # the following transformer should only add kpqnfop4aatft 3x
        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)

        word_vector_after: list = analyze_words(pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        self.assertEqual(1, word_vector_after.count("hostil"))
        self.assertEqual(3, word_vector_after.count("agtuexbuqjekk"))
        self.assertEqual(3, word_vector_after.count("kpqnfop4aatft"))

        # check now that no other features were changed
        expected_delta = {'kpqnfop4aatft': 3}
        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=expected_delta)

        self.assertEqual(len(newtransfstate.side_effects_worddict), 0)


    def test_commentbox_transformer_twice(self):
        # used to check that commentbox is not put onto an already existing commentbox.
        wordsdict1 = {'kpqnfop4aatft': 1, 'hostil': -1, 'agtuexbuqjekk': -3}
        wordsdict2 = {'kpqnfop4aatft': 2, 'hostil': -1, 'agtuexbuqjekk': -3}

        transf: Transformer = CommentBoxAddWordTransformer(logsettings = LogSettings(debug_coloring=True))
        # the following transformer should only add kpqnfop4aatft 3x
        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict1)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)
        newtransfstate.current_wordsdict=wordsdict2
        newtransfstate = transf.apply_transformer(transformationstate=newtransfstate)

        word_vector_after: list = analyze_words(pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        self.assertEqual(1, word_vector_after.count("hostil"))
        self.assertEqual(1, word_vector_after.count("agtuexbuqjekk"))
        self.assertEqual(3, word_vector_after.count("kpqnfop4aatft"))

        # check now that no other features were changed
        expected_delta = {'kpqnfop4aatft': 3, 'agtuexbuqjekk': -2}
        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=expected_delta)

        self.assertEqual(len(newtransfstate.side_effects_worddict), 0)


    def test_commentbox_transformer_just_addition_twice(self):
        wordsdict1 = {'kpqnfop4aatft': 2}
        wordsdict2 = {'kpqnfop4aatft': 1}

        transf: Transformer = CommentBoxAddWordTransformer(logsettings = LogSettings(debug_coloring=True))
        # the following transformer should only add kpqnfop4aatft 3x
        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict1)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)
        newtransfstate.current_wordsdict = wordsdict2
        newtransfstate = transf.apply_transformer(transformationstate=newtransfstate)

        word_vector_after: list = analyze_words(pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        self.assertEqual(1, word_vector_after.count("hostil"))
        self.assertEqual(3, word_vector_after.count("agtuexbuqjekk"))
        self.assertEqual(3, word_vector_after.count("kpqnfop4aatft"))

        # check now that no other features were changed
        expected_delta = {'kpqnfop4aatft': 3}
        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=expected_delta)

        self.assertEqual(len(newtransfstate.side_effects_worddict), 0)

    def test_commentbox_transformer_just_deletion(self):
        # hostile is in abstract, so should NOT be removed
        # malware is present multiple times, should be removed
        wordsdict = {'hostil': -1, 'malwar': -2}
        expected_delta = {'malwar': -2}

        word_vector_after = self.deletion_commentbox(wordsdict=wordsdict, expected_delta=expected_delta)

        self.assertEqual(1, word_vector_after.count("hostil"))
        self.assertEqual(3, word_vector_after.count("agtuexbuqjekk"))
        self.assertEqual(33 + expected_delta['malwar'], word_vector_after.count("malwar"))

    def deletion_commentbox(self, wordsdict, expected_delta) -> list:

        transf: Transformer = CommentBoxDelWordTransformer(logsettings = LogSettings(debug_coloring=True))
        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)

        word_vector_after: list = analyze_words(
            pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        # check now that no other features were changed
        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=expected_delta)

        self.assertEqual(len(newtransfstate.side_effects_worddict), 0)

        return word_vector_after

    def test_commentbox_transformer_stemming_issue(self):
        wordsdict = {'kpqnfop4aatft': 3, 'disproportion': 2, 'hostil': -1, 'agtuexbuqjekk': -3}

        transf: Transformer = CommentBoxAddWordTransformer(logsettings = LogSettings(debug_coloring=True))
        # the following transformer should only add kpqnfop4aatft 3x
        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)

        word_vector_after: list = analyze_words(pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        self.assertEqual(1, word_vector_after.count("hostil"))
        self.assertEqual(2, word_vector_after.count("agtuexbuqjekk"))
        self.assertEqual(3, word_vector_after.count("kpqnfop4aatft"))

        # check now that no other features were changed
        expected_delta = {'kpqnfop4aatft': 3, 'agtuexbuqjekk': -1, 'disproportion': 2}
        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=expected_delta)

        self.assertEqual(len(newtransfstate.side_effects_worddict), 0)
