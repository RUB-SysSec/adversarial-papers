import pathlib

from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.Transformer import Transformer
from problemspace.transformers.bibtex.BibTexDatabase import BibTexDatabase
from problemspace.transformers.bibtex.BibTexTransformer import BibTexTransformer
from problemspace.transformers.bibtex.BibTexAssignmentSolverParent import BibTexAssignmentSolverParent
from problemspace.transformers.bibtex.BibTexAssignmentSolver2 import BibTexAssignmentSolver2
from problemspace.tests.unittesting.UnitBaseClass import UnitBaseClass
from problemspace.transformers.TransformationState import TransformationState
from utils.pdf_utils import analyze_words


class TestBibTexTransformer(UnitBaseClass):
    bibtexfiles = pathlib.Path.cwd().parent / "evaluation" / "bibsources"  # TODO unique config file for that

    def setUp(self):
        """
        Runs before any test.
        """
        self.setup_all()

        self.bibtexdatabase = BibTexDatabase(verbose=True)
        self.bibtexdatabase.load_bibtexdatabase_from_pickle(
            targetfilepath=self.bibtexfiles / "bibsources_bibtextests_2_0.pck")

    def test_bibtex_transformer3(self):
        wordsdict = {'papernot': 2, 'mcdaniel': 1}

        bibtexassignmentsolver: BibTexAssignmentSolverParent = BibTexAssignmentSolver2(verbose=False, maxpapers=1)
        logsettings: LogSettings = LogSettings()
        transf: Transformer = BibTexTransformer(bibtexdatabase=self.bibtexdatabase,
                                                bibtexassignmentsolver=bibtexassignmentsolver,
                                                logsettings=logsettings)

        # the following transformer should only add papernot +1, macdaniel +1
        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)

        word_vector_after: list = analyze_words(
            pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        self.assertEqual(word_vector_after.count("hostil"), 1)
        self.assertEqual(word_vector_after.count("agtuexbuqjekk"), 3)
        self.assertEqual(word_vector_after.count("kpqnfop4aatft"), 0)

        # check now that no other features were changed
        ignore_addition_words_ = {'detect': 1, 'esor': 1, 'secur': 1, 'proc': 1, 'malwar': 1, 'manoharan': 1, 'page': 1,
                                  'back': 1, 'exampl': 1, 'comput': 1, 'research': 1, 'symposium': 1, 'adversari': 1,
                                  'gross': 1, 'european': 1, 'papernot': 1, 'mcdaniel': 1}

        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=ignore_addition_words_)

    def test_bibtex_transformer4(self):
        # we should only add 3 papers, as two are shared by papernot and mcdaniel.
        wordsdict = {'papernot': 3, 'mcdaniel': 2}

        bibtexassignmentsolver: BibTexAssignmentSolverParent = BibTexAssignmentSolver2(verbose=False, maxpapers=5)
        logsettings: LogSettings = LogSettings()
        transf: Transformer = BibTexTransformer(bibtexdatabase=self.bibtexdatabase,
                                                bibtexassignmentsolver=bibtexassignmentsolver,
                                                logsettings=logsettings)

        # the following transformer should only add papernot +1, macdaniel +1
        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)

        word_vector_after: list = analyze_words(
            pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        self.assertEqual(word_vector_after.count("hostil"), 1)
        self.assertEqual(word_vector_after.count("agtuexbuqjekk"), 3)
        self.assertEqual(word_vector_after.count("kpqnfop4aatft"), 0)

        ignore_addition_words_ = {'infer': 1, 'privaci': 1, 'wu': 1, 'symposium': 2, 'machin': 1, 'ownership': 1,
                                  'malwar': 1, 'swami': 1, 'perturb': 1, 'gross': 1, 'comput': 1, 'detect': 1,
                                  'defens': 1, 'resolut': 1, 'network': 1, 'maini': 1, 'deep': 1, 'research': 1,
                                  'exampl': 1, 'neural': 1, 'arxiv': 1, 'secur': 2, 'adversari': 2, 'manoharan': 1,
                                  'yaghini': 1, 'distil': 1, 'proc': 2, 'ieee': 1, 'european': 1, 'page': 2, 'back': 1,
                                  'dataset': 1, 'jha': 1, 'esor': 1, 'learn': 1, '10706v1': 1, 'papernot': 3,
                                  'mcdaniel': 2}

        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=ignore_addition_words_)

    def test_bibtex_transformer5(self):
        """
        Test that first name is correctly handled if first name is keyword.
        """
        wordsdict = {'nichola': 3, 'christian': 1, 'thorsten': 2}

        bibtexassignmentsolver: BibTexAssignmentSolverParent = BibTexAssignmentSolver2(verbose=False, maxpapers=5)
        logsettings: LogSettings = LogSettings()
        transf: Transformer = BibTexTransformer(bibtexdatabase=self.bibtexdatabase,
                                                bibtexassignmentsolver=bibtexassignmentsolver,
                                                logsettings=logsettings)

        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)

        word_vector_after: list = analyze_words(
            pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        self.assertEqual(word_vector_after.count("hostil"), 1)
        self.assertEqual(word_vector_after.count("agtuexbuqjekk"), 3)
        self.assertEqual(word_vector_after.count("kpqnfop4aatft"), 0)

        ignore_addition_words_ = {'mocfi': 1, 'rnberger': 1, 'dmitrienko': 1, 'www': 2, 'protocolindepend': 1,
                                  'jing': 1, 'drn': 1, 'weaver': 1, 'hrer': 1, 'control': 1, 'amplif': 1, 'yuan': 1,
                                  'zhang': 1, 'li': 1, 'adapt': 1, 'chinenyanga': 1, 'replay': 1, 'usenix': 1,
                                  'rossow': 1, 'page': 2, 'proc': 5, 'egel': 1, 'ddo': 1, 'network': 2, 'paxson': 1,
                                  'applic': 1, 'holz': 2, 'exit': 1, 'world': 2, 'reinforc': 1, 'dialog': 1,
                                  'confer': 2, 'smartphon': 1, 'elixir': 1, 'secur': 3, 'distribut': 2, 'nu': 1,
                                  'hell': 1, 'wide': 2, 'hund': 1, 'impact': 1, 'flow': 1, 'xml': 1, 'framework': 2,
                                  'mitig': 1, 'cui': 1, 'katz': 1, 'news': 1, 'ndss': 2, 'recommend': 1, 'databas': 1,
                                  'base': 1, 'symposium': 3, 'xiang': 1, 'web': 2, 'attack': 2, 'xie': 1, 'davi': 1,
                                  'hupperich': 1, 'reduc': 1, 'queri': 1, 'intern': 2, 'fischer': 1, 'kushmerick': 1,
                                  'deep': 1, 'similar': 1, 'use': 1, 'system': 2, 'learn': 1, 'sadeghi': 1, 'ku': 1,
                                  'zheng': 2,
                                  'christian': 1, 'nichola': 3, 'thorsten': 2
                                  }

        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=ignore_addition_words_)
