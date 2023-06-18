from problemspace.tests.unittesting.UnitBaseClass import UnitBaseClass
from problemspace.transformers.CommentBoxDelWordTransformer import \
    CommentBoxDelWordTransformer
from problemspace.transformers.HomoglyphTransformer import HomoglyphTransformer
from problemspace.transformers.IgnoredEnvironments import IGNORED_ENVS
from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.ReplacementTransform import (
    create_inside_ignored, merge)


class TestReplacementTransformer(UnitBaseClass):
    def setUp(self):
        """
        Runs before any test.
        """
        self.setup_all()

    # def test_special_case(self):
    #     with open("problemspace/tests/unittesting/documents/1807.00477a") as f:
    #         doc_a = f.read()
    #
    #     with open("problemspace/tests/unittesting/documents/1807.00477b") as f:
    #         doc_b = f.read()
    #
    #     transformer = HomoglyphTransformer(logsettings=LogSettings(),
    #                                        ignored_environments=IGNORED_ENVS)
    #
    #     tokenizer = transformer._build_tokenizer()
    #     stemmer = transformer._build_stemmer()
    #     replacements = transformer._build_replacements()
    #
    #     wordsdict = {"buf": -3}
    #
    #     _, feature_delta_a = transformer._find_transforms(
    #         doc_a, wordsdict, stemmer, tokenizer, replacements)
    #
    #     _, feature_delta_b = transformer._find_transforms(
    #         doc_b, wordsdict, stemmer, tokenizer, replacements)
    #
    #     self.assertEqual(feature_delta_a.changes, feature_delta_b.changes)
    #     self.assertEqual(feature_delta_a.changes.get("buf"), -3)

    def test_ignoring(self):
        doc = r"""\begin{comment}\begin{lstlisting}\end{comment}"""

        ignored_environments = ["lstlisting", "comment"]

        transformer = HomoglyphTransformer(logsettings=LogSettings())
        ignored_section = transformer._find_ignored_env_sections(
            doc, 0, len(doc), ignored_environments=ignored_environments)

        self.assertEqual(ignored_section, [(0, len(doc))])

    def test_ignoring2(self):
        doc = r"""\begin{comment}\begin{comment}\begin{comment}\begin{lstlisting}\end{comment}\begin{lstlisting}\end{comment}\end{lstlisting}"""

        ignored_environments = ["lstlisting", "comment"]

        transformer = HomoglyphTransformer(logsettings=LogSettings())
        ignored_section = transformer._find_ignored_env_sections(
            doc, 0, len(doc), ignored_environments=ignored_environments)

        self.assertEqual(ignored_section, [(0, 76), (76, len(doc))])

    # def test_ignore_quickmath_doc_0(self):
    #     with open("problemspace/tests/unittesting/documents/2108.13818") as f:
    #         doc = f.read()
    #
    #     transformer = CommentBoxDelWordTransformer(logsettings=LogSettings())
    #     featuredelta, transforms = transformer._transform_main_part(
    #         doc, {"fence": -10})
    #
    #     # TODO: self.assertEquals(featuredelta)
    #
    # def test_ignore_quickmath_doc_1(self):
    #     with open("problemspace/tests/unittesting/documents/2108.13818") as f:
    #         doc = f.read()
    #
    #     transformer = CommentBoxDelWordTransformer(logsettings=LogSettings())
    #     featuredelta, transforms = transformer._transform_main_part(
    #         doc, {"SMT": -10})
    #
    #     # TODO: self.assertEquals(featuredelta)
    #
    # def test_ignore_quickmath_doc_2(self):
    #     with open("problemspace/tests/unittesting/documents/2112.03449") as f:
    #         doc = f.read()
    #
    #     transformer = CommentBoxDelWordTransformer(
    #         logsettings=LogSettings(), ignored_environments=IGNORED_ENVS)
    #     featuredelta, transforms = transformer._transform_main_part(
    #         doc, {"SMT": -10})
    #
    #     # TODO: self.assertEquals(featuredelta)

    def test_ignore_quickmath_0(self):
        doc = r"{ignore this} not this $$\{$$ {ignore this} ---- {ignore} \[\{\] {ignore} not this"

        ignored_environments = []
        transformer = HomoglyphTransformer(logsettings=LogSettings())

        ignored_env_sections = transformer._find_ignored_env_sections(
            doc,
            0,
            len(doc),
            ignored_environments=ignored_environments,
            ignore_quick_math=True)

        self.assertEqual(ignored_env_sections, [(23, 29), (58, 64)])

        inside_ignored = create_inside_ignored(ignored_env_sections)
        brackets = transformer._find_active_brackets(doc, 0, len(doc),
                                                     inside_ignored)
        assert len(brackets) == 0 or brackets[0][1] == "{"

        exp_brackets = [(0, "{"), (12, "}"), (30, "{"), (42, "}"), (49, "{"),
                        (56, "}"), (65, "{"), (72, "}")]

        for bracket, exp_bracket in zip(brackets, exp_brackets):
            self.assertEqual(bracket, exp_bracket)

        bracket_ignore_sections = transformer._match_brackets_to_sections(
            brackets)
        self.assertEqual(bracket_ignore_sections, [(0, 13), (30, 43), (49, 57),
                                                   (65, 73)])

        ignored_sections, _ = transformer._find_ignored_sections(
            doc,
            0,
            len(doc),
            ignored_environments=ignored_environments,
            check_within_cmd=True,
            ignore_quick_math=True)

        self.assertEqual(ignored_sections, [(0, 13), (23, 29), (30, 43),
                                            (49, 57), (58, 64), (65, 73)])

    def test_ignore_quickmath_1(self):
        doc = r"{ignore this} not this $$\{$$ \begin{lstlisting}Some words\end{lstlisting}"

        transformer = HomoglyphTransformer(logsettings=LogSettings())
        ignored_environments = ["lstlisting"]

        ignored_env_sections = transformer._find_ignored_env_sections(
            doc,
            0,
            len(doc),
            ignored_environments=ignored_environments,
            ignore_quick_math=True)

        self.assertEqual(ignored_env_sections, [(23, 29), (30, 74)])

        inside_ignored = create_inside_ignored(ignored_env_sections)
        brackets = transformer._find_active_brackets(doc, 0, len(doc),
                                                     inside_ignored)
        assert len(brackets) == 0 or brackets[0][1] == "{"

        exp_brackets = [(0, "{"), (12, "}")]

        for bracket, exp_bracket in zip(brackets, exp_brackets):
            self.assertEqual(bracket, exp_bracket)

        bracket_ignore_sections = transformer._match_brackets_to_sections(
            brackets)
        self.assertEqual(bracket_ignore_sections, [(0, 13)])

        ignored_sections, _ = transformer._find_ignored_sections(
            doc,
            0,
            len(doc),
            ignored_environments=ignored_environments,
            check_within_cmd=True,
            ignore_quick_math=True)

        self.assertEqual(ignored_sections, [(0, 13), (23, 29), (30, 74)])

    def test_bracket_ignore(self):
        doc = r"{Ignore}{Ignore this {and this} too}"

        transformer = HomoglyphTransformer(logsettings=LogSettings())
        brackets = transformer._find_active_brackets(doc, 0, len(doc))

        self.assertEqual(brackets, [(0, "{"), (7, "}"), (8, "{"), (21, "{"),
                                    (30, "}"), (35, "}")])

        bracket_ignore_sections = transformer._match_brackets_to_sections(
            brackets)
        self.assertEqual(bracket_ignore_sections, [(0, 8), (8, 36)])

    def test_ignore_comments(self):
        doc = "{Ignore}% do not parse this -> { \n {Ignore this {and this} too} \n% Ignore }} \n"

        transformer = HomoglyphTransformer(logsettings=LogSettings())
        ignored_sections, _ = transformer._find_ignored_sections(
            doc,
            0,
            len(doc), [],
            check_within_cmd=True,
            ignore_quick_math=True)

        self.assertEqual(ignored_sections, [(0, 8), (8, 34), (35, 63), (65, 78)])

    def test_handle_brackets(self):
        doc = r"\begin{lstlisting}int foo() {\end{lstlisting} Text{ignored} {Ignore this {and this} too} End."
        ignored_environments = ["lstlisting"]
        transformer = HomoglyphTransformer(logsettings=LogSettings())

        ignored_env_sections = transformer._find_ignored_env_sections(
            doc, 0, len(doc), ignored_environments=ignored_environments)

        self.assertEqual(ignored_env_sections, [(0, 45)])

        inside_ignored = create_inside_ignored(ignored_env_sections)
        brackets = transformer._find_active_brackets(doc, 0, len(doc),
                                                     inside_ignored)
        assert len(brackets) == 0 or brackets[0][1] == "{"

        self.assertEqual(brackets, [(50, "{"), (58, "}"), (60, "{"), (73, "{"),
                                    (82, "}"), (87, "}")])

        bracket_ignore_sections = transformer._match_brackets_to_sections(
            brackets)
        self.assertEqual(bracket_ignore_sections, [(50, 59), (60, 88)])

        ignored_sections, _ = transformer._find_ignored_sections(
            doc,
            0,
            len(doc),
            ignored_environments=ignored_environments,
            check_within_cmd=True)

        self.assertEqual(ignored_sections, [(0, 45), (50, 59), (60, 88)])

    def test_ignore_bracket_synonym(self):
        ignored_environments = ["comment", "lstlisting"]

        transformer = HomoglyphTransformer(
            logsettings=LogSettings(),
            ignored_environments=["comment", "lstlisting"])

        doc = r"begin \begin{comment}\begin{lstlisting}insensitive{\end{comment}\begin{comment}\end{comment} {this is insensitive and in brackets}"

        ignored_sections, _ = transformer._find_ignored_sections(
            doc,
            0,
            len(doc),
            ignored_environments=ignored_environments,
            check_within_cmd=True)

        self.assertEqual(ignored_sections, [(6, 64), (64, 92), (93, 130)])

    def test_ignore_bracket_offset_synonym(self):
        ignored_environments = ["comment", "lstlisting"]

        transformer = HomoglyphTransformer(
            logsettings=LogSettings(),
            ignored_environments=ignored_environments)

        doc = r"begin \begin{comment}\begin{lstlisting}insensitive{\end{comment}\begin{comment}\end{comment} {this is insensitive and in brackets}"

        ignored_sections, _ = transformer._find_ignored_sections(
            doc,
            92,
            len(doc),
            ignored_environments=ignored_environments,
            check_within_cmd=True)

        self.assertEqual(ignored_sections, [(93, 130)])

    def test_ignore_bordering_brackets(self):
        ignored_environments = ["lstlisting"]

        transformer = HomoglyphTransformer(
            logsettings=LogSettings(),
            ignored_environments=ignored_environments)

        doc = r"{Ignore this}\begin{lstlisting}\end{lstlisting}{And this} but not this"

        ignored_sections, _ = transformer._find_ignored_sections(
            doc,
            0,
            len(doc),
            ignored_environments=ignored_environments,
            check_within_cmd=True)

        self.assertEqual(ignored_sections, [(0, 13), (13, 47), (47, 57)])
