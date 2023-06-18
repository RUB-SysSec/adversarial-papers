from typing import Dict, List, Tuple

from problemspace.tests.unittesting.UnitBaseClass import UnitBaseClass
from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.SynonymTransformer import SynonymTransformer
from problemspace.transformers.TransformationState import TransformationState
from utils.pdf_utils import analyze_words

Similarity = float
Word = str
Synonym = str


class MockupSynonym:
    def __init__(self, synonyms: Dict[Word, List[Tuple[Synonym, Similarity]]]):
        self.wv = MockupSynonym.MockupWordVector(synonyms)

    class MockupWordVector:
        def __init__(self, synonyms):
            self.synonyms = synonyms

        def most_similar(self, word):
            return self.synonyms[word]


class TestSynonymTransformer(UnitBaseClass):
    def setUp(self):
        """
        Runs before any test.
        """
        self.setup_all()

    def test_add_synonyms(self):
        transformer = SynonymTransformer(logsettings=LogSettings())

        tokenizer = transformer._build_tokenizer()
        stemmer = transformer._build_stemmer()
        synonym_model = MockupSynonym({"adversary": [["attacker", 1]]})

        doc = "\\begin{document}An adversary detects an intrusion \\end{document}"
        wordsdict = {"attack": 1}

        transforms, feature_delta = transformer._find_transforms(
            doc, wordsdict, stemmer, tokenizer, synonym_model)
        new_doc = transformer._apply_transforms(doc, transforms)

        self.assertEqual(feature_delta.changes.get("attack"), 1)
        self.assertEqual(doc.replace("adversary", "attacker"), new_doc)

    def test_synonym_transformer(self):
        wordsdict = {'attack': -5, 'agtuexbuqjekk': -5}
        transf = SynonymTransformer(logsettings=LogSettings(), pos_checker=1)

        # the following transformer should only add kpqnfop4aatft 3x
        transfstate: TransformationState = TransformationState(
            pdflatexsource=self.newpdflatexsource,
            original_wordsdict=wordsdict)



        newtransfstate = transf.apply_transformer(
            transformationstate=transfstate)



        word_vector_after: list = analyze_words(
            pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(
                suffix="pdf"))

        self.assertEqual(self.word_vector_before.count("attack"), 31)
        self.assertEqual(word_vector_after.count("attack"), 30)

        self.assertEqual(self.word_vector_before.count("adversari"), 16)
        self.assertEqual(word_vector_after.count("adversari"), 17)
        self.assertEqual(word_vector_after.count("agtuexbuqjekk"), 3)

        expected_delta = {"adversari": 1, "attack": -1}

        # check now that no other features were changed:
        UnitBaseClass.check_counts_before_and_after_valuebased(
            word_vector_before=self.word_vector_before,
            word_vector_after=word_vector_after,
            ignore_words=expected_delta)

    def test_ignore_lstlisting(self):
        transformer = SynonymTransformer(logsettings=LogSettings(),
                                         ignored_environments=["lstlisting"])

        tokenizer = transformer._build_tokenizer()
        stemmer = transformer._build_stemmer()

        synonym_model = MockupSynonym({
            "insensitive": [["unfeeling", 1], ["inconsiderate", 1]],
            "begin": [["start", 1]]
        })

        doc = """
            \\documentclass{article}
            \\usepackage{listings}
            \\begin{document}
            \\lstset{language=Pascal}

            \\begin{lstlisting}[frame=single]
            for i:=maxint to 0 do
            begin
            { do nothing }
            end;
            Write('Case insensitive ');
            Write('Pascal keywords.');
            \\end{lstlisting}

            some more text begin

            \\end{document}
        """
        wordsdict = {"insensit": -1, "begin": -1}

        _, feature_delta = transformer._find_transforms(
            doc, wordsdict, stemmer, tokenizer, synonym_model)

        self.assertEqual(feature_delta.changes.get("begin"), -1)
        self.assertEqual(feature_delta.changes.get("insensit", 0), 0)

    def test_ignore_comment(self):
        transformer = SynonymTransformer(logsettings=LogSettings(),
                                         ignored_environments=["comment"])

        tokenizer = transformer._build_tokenizer()
        stemmer = transformer._build_stemmer()

        synonym_model = MockupSynonym({
            "insensitive": [["unfeeling", 1], ["inconsiderate", 1]],
            "begin": [["start", 1]]
        })

        doc = """\\documentclass{sig-alternate}
        \\begin{document}begin
        \\begin{comment}insensitive\\end{comment}
        \\begin{comment}\\end{comment}
        \\end{document}
        """

        wordsdict = {"insensit": -1, "begin": -1}

        _, feature_delta = transformer._find_transforms(
            doc, wordsdict, stemmer, tokenizer, synonym_model)

        self.assertEqual(feature_delta.changes.get("begin"), -1)
        self.assertEqual(feature_delta.changes.get("insensit", 0), 0)

    def test_ignore_comment_special(self):
        transformer = SynonymTransformer(
            logsettings=LogSettings(),
            ignored_environments=["comment", "lstlisting"])

        tokenizer = transformer._build_tokenizer()
        stemmer = transformer._build_stemmer()

        synonym_model = MockupSynonym({
            "insensitive": [["unfeeling", 1], ["inconsiderate", 1]],
            "begin": [["start", 1]]
        })

        doc = r"""\documentclass{sig-alternate}\begin{document}begin \begin{comment}\begin{lstlisting}insensitive\end{comment}\begin{comment}\end{comment}\end{document}"""

        wordsdict = {"insensit": -1, "begin": -1}

        _, feature_delta = transformer._find_transforms(
            doc, wordsdict, stemmer, tokenizer, synonym_model)

        self.assertEqual(feature_delta.changes.get("begin"), -1)
        self.assertEqual(feature_delta.changes.get("insensit", 0), 0)

    def test_ignore_comment_special2(self):
        transformer = SynonymTransformer(
            logsettings=LogSettings(),
            ignored_environments=["comment", "lstlisting"])

        tokenizer = transformer._build_tokenizer()
        stemmer = transformer._build_stemmer()

        synonym_model = MockupSynonym({
            "insensitive": [["unfeeling", 1], ["inconsiderate", 1]],
            "begin": [["start", 1]]
        })

        doc = """\\documentclass{sig-alternate}
        \\begin{document}begin
        \\begin{comment}\\begin{lstlisting}insensitive{\\end{comment}
        \\begin{comment}\\end{comment}
        {this is insensitive and in brackets}
        \\end{document}
        """

        wordsdict = {"insensit": -1, "begin": -1}

        _, feature_delta = transformer._find_transforms(
            doc, wordsdict, stemmer, tokenizer, synonym_model)

        self.assertEqual(feature_delta.changes.get("begin"), -1)
        self.assertEqual(feature_delta.changes.get("insensit", 0), 0)
