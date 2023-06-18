import re
from abc import abstractmethod
from typing import List, Optional, Dict, Set
import collections

from nltk.stem import PorterStemmer
from nltk.tokenize import TreebankWordTokenizer, WhitespaceTokenizer
from problemspace.exceptions.TransformerException import TransformerException
from problemspace.transformers.FeatureDelta import FeatureDelta
from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.Transformer import Transformer
from itertools import takewhile

class TooManyClosingBracketException(RuntimeError):
    def __init__(self, brackets, bracket_states):
        assert len(brackets) == len(bracket_states)
        assert bracket_states[-1] < 0

        self.brackets = brackets
        self.bracket_states = bracket_states

    def __str__(self):
        for (pos, bracket), bracket_state in zip(self.brackets, self.bracket_states):
            if bracket_state < 0:
                return f"TooManyClosingBracketException: {bracket}, {pos}"

        return "TooManyClosingBracketException: invalid"

class UnmatchedBracketsException(RuntimeError):
    def __init__(self, brackets, bracket_states):
        assert len(brackets) == len(bracket_states)
        assert bracket_states[-1] > 0

        self.brackets = brackets
        self.bracket_states = bracket_states

    def __str__(self):
        last_state = self.bracket_states[-1]

        predicate = lambda x: x >= last_state
        faulty_states = list(takewhile(predicate, self.bracket_states[::-1]))
        faulty_states = faulty_states[::-1]

        start = -len(faulty_states) - 1
        end = -len(faulty_states) + 2
        first_faulty = self.brackets[start:end]

        return f"UnmatchedBracketsException: Fault begins around {first_faulty}"

class TransformInfo:
    def __init__(self, token_start, token_end, token, stem, new_token,
                 new_stem):
        assert token != new_token, "Transformation does not change token ({token})"

        self.token_start = token_start
        self.token_end = token_end
        self.token = token
        self.stem = stem
        self.new_token = new_token
        self.new_stem = new_stem

    def __repr__(self) -> str:
        return f"TransformInfo({self.token_start},{self.token_end},{self.token},{self.new_token})"


class ReplacementTransformer(Transformer):
    def __init__(self,
                 logsettings: LogSettings,
                 ignored_environments: List[str],
                 stemmer=None,
                 tokenizer=None):

        super().__init__(logsettings=logsettings)
        self.stemmer = stemmer
        self.tokenizer = tokenizer
        self.ignored_environments = ignored_environments

    @abstractmethod
    def _transform(self,
                   transformationstate: TransformationState) -> FeatureDelta:
        pass

    @staticmethod
    def _apply_transforms(doc: str, transforms: List[TransformInfo]):
        new_doc = []

        # since python uses immutable strings we sligthly optimize the replacement
        # by first sorting the replacement indices in ascending order...
        transforms = sorted(transforms, key=lambda x: x.token_start)

        # ...then we iterate from left to right (since indices are ascending)
        # through the string and saving the slices between replacements in a
        # list.
        left_bound = 0
        for transform in transforms:
            new_doc.append(doc[left_bound:transform.token_start])
            new_doc.append(transform.new_token)

            left_bound = transform.token_end
        new_doc.append(doc[left_bound:])

        # This is faster than:
        #  - replacing each homoglyph separatly (since it requires a lot of string copies)
        #  - converting the doc to a list, replacing characters in this list and
        #    joining them "".join(list)
        return "".join(new_doc)

    def _get_problemspace_constraints(self, doc: str, wordsdict: Dict[str, int]) -> Set:
        """
        Get generic problem-space constraints for specific features.
        Here, we test if words in wordsdict exist that are not part of the parsed document.
        This means that these words were ignored and thus cannot be removed.
        Note that we can add any word in theory with other transformers,
        so here we only block negative words in wordsdict.
        """
        tokenizer = self._build_tokenizer()
        stemmer = self._build_stemmer()
        strict: bool = False

        token_list = list(
            self._iterate_over_document(
                doc=doc,
                tokenizer=tokenizer,
                check_within_cmd=True))

        if strict is True:
            tokens = set([stemmer.stem(token) for _, _, token in token_list])
            wordsdict_set = set([k for k,v in wordsdict.items() if v < 0])
            return wordsdict_set.difference(tokens)
        else:
            threshold = 0.5
            tokens = [stemmer.stem(token) for _, _, token in token_list]
            tokens_counter = collections.Counter(tokens)

            blocked_words = set()
            for tkey, tval in wordsdict.items():
                if tval < 0:
                    if tokens_counter[tkey] <= (-1) * threshold * tval:
                        blocked_words.add(tkey)
            return blocked_words

    def _iterate_over_document(self,
                               doc: str,
                               tokenizer,
                               check_within_cmd: bool,
                               ignore_quick_math=True):
        """
        Generator for tokens from document.
        :param doc: latex document as string
        :param tokenizer: tokenizer
        :param check_within_cmd: if true, checked if current token is within latex command, e.g. \textbf{}.
        If so, it would not use this token.
        :return: token-start, token-end, token string.
        """
        ignored_environments: List[str] = self.ignored_environments

        # Find suitable location for replacement,
        # retrieve begin and end of document (we only want to edit the content)
        content_start = doc.index("\\begin{document}") + len(
            "\\begin{document}")
        content_end = doc.index("\\end{document}")
        assert content_start <= content_end

        # find end of abstract (we do not want to modify the abstract)
        abstract_end = doc.find("\\end{abstract}")
        if abstract_end > 0:
            abstract_end += len("\\end{abstract}")
        else:
            # try to find first relevant section if abstract was not defined as environment
            firstsectionindexrange = re.search(r"\\section{.*}", doc)
            if firstsectionindexrange is not None:
                abstract_end = firstsectionindexrange.end()

        _, inside_ignored = self._find_ignored_sections(
            doc, content_start, content_end, ignored_environments,
            check_within_cmd, ignore_quick_math)

        # tokenize and sort by token_start position
        try:
            token_spans = list(tokenizer.span_tokenize(doc))
        except ValueError:
            default_tokenizer = WhitespaceTokenizer()
            token_spans = list(default_tokenizer.span_tokenize(doc))
        token_spans.sort(key=lambda x: x[0])

        for token_start, token_end in token_spans:
            # we are only interested in tokens inside the latex document
            if token_start < content_start or content_end < token_end:
                continue

            if token_start < abstract_end:
                continue

            if inside_ignored(token_start, token_end):
                continue

            token = doc[token_start:token_end]
            yield token_start, token_end, token

    @classmethod
    def _find_ignored_sections(cls,
                               doc,
                               content_start,
                               content_end,
                               ignored_environments,
                               check_within_cmd,
                               ignore_quick_math=True):
        """
        This function finds every section that is to be ignored when generating
        tokens. The [ignored_environments] parameter defines the latex environments
        that are to be ignored (e.g. everything inside an lstlisting or comment block).
        The [check_within_cmd] parameter defines whether text inside curly brackets
        should be ignored; this would prevent replacing text in e.g. \section{} elements.
        """
        comment_sections = list(cls._find_comments(doc))
        is_inside_comment = create_inside_ignored(comment_sections)

        ignored_env_sections = cls._find_ignored_env_sections(
            doc, content_start, content_end, ignored_environments,
            ignore_quick_math, is_inside_comment)

        assert all(ignored_env_sections[i][0] < ignored_env_sections[i][1] <=
                   ignored_env_sections[i + 1][0]
                   for i in range(0,
                                  len(ignored_env_sections) - 1))

        is_inside_env = create_inside_ignored(ignored_env_sections)

        if check_within_cmd:
            ignored_sections = cls._handle_brackets(doc, content_start,
                                                    content_end, is_inside_env,
                                                    ignored_env_sections,
                                                    is_inside_comment,
                                                    comment_sections)
        else:
            ignored_sections = ignored_env_sections

        return ignored_sections, create_inside_ignored(ignored_sections)

    @classmethod
    def _handle_brackets(cls,
                         doc,
                         content_start,
                         content_end,
                         is_inside_ignored,
                         ignored_sections,
                         is_inside_comment=None,
                         comment_sections=[]):
        """
        This functions adds sections that are enclosed by brackets to the
        ignore-list. This list already contains sections that are ignored because
        they belong to environment blocks.
        """
        brackets = cls._find_active_brackets(doc, content_start, content_end,
                                             is_inside_ignored,
                                             is_inside_comment)
        assert len(brackets) == 0 or brackets[0][1] == "{"

        bracket_ignore_sections = cls._match_brackets_to_sections(brackets)

        return merge(
            merge(ignored_sections, bracket_ignore_sections,
                  lambda x, y: x[0] < y[0]), comment_sections,
            lambda x, y: x[0] < y[0])

    @classmethod
    def _match_brackets_to_sections(cls, brackets):
        """
        Matches each top-most opening bracket to its corresponding enclosing
        bracket.
        """
        bracket_ignore_sections = []
        bracket_state = 0
        bracket_start, bracket_end = None, None

        bracket_states = []

        for pos, bracket in brackets:
            if bracket == "{":
                bracket_state += 1

                if bracket_state == 1:
                    bracket_start = pos

            elif bracket == "}":
                bracket_state -= 1

                if bracket_state == 0:
                    bracket_end = pos + 1
            else:
                assert False

            bracket_states.append(bracket_state)

            if bracket_end is not None:
                assert bracket_start is not None
                bracket_ignore_sections.append((bracket_start, bracket_end))
                bracket_start, bracket_end = None, None

        if bracket_state < 0:
            raise TooManyClosingBracketException(brackets, bracket_states)

        if bracket_state != 0:
            raise UnmatchedBracketsException(brackets, bracket_states)

        return bracket_ignore_sections

    @staticmethod
    def _find_comments(doc):
        # TODO: This will probably need to be expanded to \iffalse...\fi blocks

        pos = 0
        while (s := doc.find("%", pos)) != -1:
            if doc[s-1] == "\\":
                pos = s + 1
                continue

            e = doc.find("\n", s)

            if e == -1:
                yield (s, len(doc))
            else:
                yield (s, e + 1)

            pos = e + 1

    @staticmethod
    def _find_active_brackets(doc,
                              content_start,
                              content_end,
                              is_inside_ignored=None,
                              is_inside_comment=None):
        """
        Finds every bracket in the document that is not already ignored by an
        environment block
        """
        all_brackets = ((i + content_start, c)
                        for i, c in enumerate(doc[content_start:content_end])
                        if (c == "{" or c == "}"))

        active_brackets = all_brackets

        if is_inside_ignored is not None:
            active_brackets = filter(
                lambda x: not is_inside_ignored(x[0], x[0] + 1),
                active_brackets)

        if is_inside_comment is not None:
            active_brackets = filter(
                lambda x: not is_inside_comment(x[0], x[0] + 1),
                active_brackets)

        return list(active_brackets)

    @classmethod
    def _find_ignored_env_sections(cls,
                                   doc,
                                   content_start,
                                   content_end,
                                   ignored_environments,
                                   ignore_quick_math=False,
                                   is_inside_comment=None):
        """
        Finds non-overlapping sections that are enclosed by the boundaries defined
        in the parameter [ignored_environments].
        """

        # Since everything inside <ignore_boundary></ignore_boundary> is
        # discarded, ignore environments can not be enclosed inside each other.
        #
        # For example:
        #
        # \begin{comment}\begin{comment}\end{comment}\end{comment}
        # >-----------------------------------------<
        # Everything inside this section is discarded
        #
        # This also means, that we can not use this function to ignore strings
        # inside curly brackets, since these constructs are fairly common.
        #
        # \textbf{This should be ignored \emph{but this leads to errors}}
        #
        # For curly brackets we have to use a context-free approach

        ignore_boundaries = [[f"\\begin{{{env}}}", f"\\end{{{env}}}"]
                             for env in ignored_environments]

        if ignore_quick_math:
            math_brackets = [["\[", "\]"], ["$$", "$$"]]
            ignore_boundaries += math_brackets

        begin_tag_positions = cls._find_begin_positions(
            doc, content_start, content_end, ignore_boundaries)

        ignored_sections = []

        ptr = content_start
        for begin_pos, begin_tag, end_tag in begin_tag_positions:
            if begin_pos < ptr:
                continue

            if is_inside_comment is not None:
                if is_inside_comment(begin_pos, begin_pos + len(begin_tag)):
                    continue

            if cls._is_behind_escaping_backslash(begin_pos, doc):
                continue

            end_pos = doc.find(end_tag, begin_pos + len(begin_tag),
                               content_end)

            assert end_pos >= 0, f"Did not find end_pos for {begin_tag} and {end_tag} after character ({begin_pos})"

            ptr = end_pos + len(end_tag)
            ignored_sections.append((begin_pos, ptr))

        return ignored_sections

    @staticmethod
    def _is_behind_escaping_backslash(begin_pos, doc):
        """
        This function is a quick fix to differentiate between "\[" and "\\[5em]".
        The former is opening a math sequence while the latter defines a linebreak.
        """

        if begin_pos <= 0:
            return False

        if doc[begin_pos - 1] == "\\":
            return True

        return False

    @staticmethod
    def _find_begin_positions(doc, content_start, content_end,
                              ignore_boundaries):
        begin_tag_positions = []

        for begin_tag, end_tag in ignore_boundaries:
            search_start = content_start

            while True:
                pos = doc.find(begin_tag, search_start, content_end)

                if pos < 0:
                    break

                search_start = pos + len(begin_tag)
                begin_tag_positions.append((pos, begin_tag, end_tag))

        begin_tag_positions.sort(key=lambda x: x[0])

        return begin_tag_positions

    def _build_tokenizer(self):
        if self.tokenizer is None:
            return TreebankWordTokenizer()
        else:
            return self.tokenizer

    def _build_stemmer(self):
        if self.stemmer is None:
            return PorterStemmer()
        else:
            return self.stemmer

    @staticmethod
    def _find_last_documentclass(doc):
        last_match = None
        offset = 0

        while True:
            m = re.search(r"\\documentclass.*?{.*?}.*\n", doc[offset:])

            if m is None:
                break
            else:
                last_match = m
                offset += m.end()

        if last_match is None:
            raise TransformerException("No \documentclass command found")

        return offset

    @staticmethod
    def _enable_debug_coloring(doc: str, default_insert_pos: int) \
            -> Optional[TransformInfo]:
        """
        Enables coloring by creating color command in header of document.
        Checks if command is already present.
        :param doc: latex document
        :param default_insert_pos: index position where it should be included
        :return: TransformInfo
        """
        if "\\newcommand{\\debugcolor}[1]{\\color{#1}}" not in doc:

            newcmd = "\\newcommand{\\debugcolor}[1]{\\color{#1}}\n"

            # check if xcolor is already loaded
            m = re.search(r"\\usepackage.*?{xcolor}.*\n", doc)
            if m is None:
                newcmd = "\\usepackage{xcolor}\n" + newcmd

            return TransformInfo(default_insert_pos, default_insert_pos, "",
                                 "", newcmd, "")

        return None


def create_inside_ignored(ignored_sections):
    """
    Creates a function that checks whether a token (defined by [token_start] and
    [token_end]) overlaps with any of the section is [ignored_sections].
    """
    def non_overlap(a, b, c, d):
        # token0 = doc[a:b]
        # token1 = doc[c:d]
        return b <= c or d <= a

    def fn(token_start, token_end):
        return any(not non_overlap(token_start, token_end, s, e)
                   for s, e in ignored_sections)

    return fn


def merge(a, b, is_smaller):
    """
    Merge to sorted list [a] and [b] (sorted according to [is_smaller])
    """
    c = []

    i = 0
    j = 0

    while i < len(a) and j < len(b):
        if is_smaller(a[i], b[j]):
            c.append(a[i])
            i += 1
        else:
            c.append(b[j])
            j += 1

    while i < len(a):
        c.append(a[i])
        i += 1

    while j < len(b):
        c.append(b[j])
        j += 1

    return c
