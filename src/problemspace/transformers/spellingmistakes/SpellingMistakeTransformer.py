import random
import typing
from copy import copy
from typing import List, Optional, Tuple
import enum

from problemspace.transformers.LogSettings import LogSettings
from problemspace.exceptions.TransformerException import TransformerException
from problemspace.transformers.spellingmistakes.TypoGenerator import TypoGenerator
from problemspace.transformers.FeatureDelta import FeatureDelta
from problemspace.transformers.ReplacementTransform import (
    ReplacementTransformer, TransformInfo)
from problemspace.transformers.TransformationState import TransformationState


class SpellingMistakeTransformerOption(enum.Enum):
    """
    Options for SpellingMistakeTransformer.
    SWAP_LETTERS: Swap two adjacent letters, e.g. awesome -> aweosme ('so' -> 'os').
    DELETE_LETTER: Delete a random letter, e.g. awesome -> awsome ('e' deleted).
    SWAP_OR_DELETE_RANDOMLY: Choose one of the two options {SWAP_LETTERS, DELETE_LETTER} randomly.
    COMMON_TYPOS: Use only common typos in english language, e.g. -> basically -> basicly.
    COMMON_TYPOS_OTHERWISE_TRY_RANDOMLY_SWAP_DELETE: Try COMMON_TYPOS, if not possible, use SWAP_OR_DELETE_RANDOMLY.
    Note: We do not change the first and last letter of a word.
    """
    SWAP_LETTERS = 1
    DELETE_LETTER = 2
    SWAP_OR_DELETE_RANDOMLY = 3
    COMMON_TYPOS = 4
    COMMON_TYPOS_OTHERWISE_TRY_RANDOMLY_SWAP_DELETE = 5


class SpellingMistakeTransformer(ReplacementTransformer):
    """
    Changes a word by creating spelling mistakes.
    Allows us to remove features.

    Implements the Delete and Swap strategies from Li et al. (https://arxiv.org/pdf/1812.05271.pdf).
    Implements common typos, as given in TypoGenerator.py.
    See 'SpellingMistakeTransformerOption' for more information about the possible mistakes.
    Remind that we need to consider that we are working on stems when finding the spelling mistakes.
    """

    def __init__(self,
                 transformeroption: SpellingMistakeTransformerOption,
                 logsettings: LogSettings,
                 replacements=None,
                 seed=42,
                 max_changes=None,
                 ignored_environments=[],
                 *args,
                 **kwargs):

        super().__init__(logsettings=logsettings,
                         ignored_environments=ignored_environments,
                         *args,
                         **kwargs)
        self.replacements = replacements
        self.random = random.Random(seed)
        self.mistake_type: SpellingMistakeTransformerOption = transformeroption
        self.max_changes: typing.Optional[int] = max_changes

    def _transform(self,
                   transformationstate: TransformationState) -> FeatureDelta:
        tokenizer = self._build_tokenizer()
        stemmer = self._build_stemmer()

        # read main doc
        doc = transformationstate.pdflatexsource.get_main_document()

        # enable color for debug coloring
        doc = self._enable_spellingmistakes(doc, debug_coloring=self.debug_coloring)

        # find transforms
        transforms, featuredelta = self._find_transforms(
            doc,
            transformationstate.current_wordsdict,
            stemmer=stemmer,
            tokenizer=tokenizer)

        # apply transforms
        doc = self._apply_transforms(doc, transforms)

        # save main doc
        transformationstate.pdflatexsource.save_latex(doc)

        # return the wordsdict delta
        return featuredelta

    def _apply_swap_or_delete(self, token, stem, stemmer):
        """
        A small help function for swap-or-delete strategy.
        """
        if self.random.randint(0, 1) == 1:
            out_strategy = self._delete_letter(token=token, stem=stem, stemmer=stemmer)
        else:
            out_strategy = self._swap_letters(token=token, stem=stem, stemmer=stemmer)
        return out_strategy

    def _find_transforms(
            self, doc, wordsdict, stemmer, tokenizer) -> Tuple[List[TransformInfo], FeatureDelta]:
        # copy wordsdict and make sure that we operate on the word stems
        stemsdict = copy(wordsdict)

        feature_delta: FeatureDelta = FeatureDelta()

        # get generic restrictions
        blockedfeatures: set = self._get_problemspace_constraints(doc=doc, wordsdict=wordsdict)
        feature_delta.unrealizable_words.update(blockedfeatures)

        transforms = []

        token_generator = self._iterate_over_document(doc=doc,
                                                      tokenizer=tokenizer,
                                                      check_within_cmd=True)

        # Iterate over document and its tokens
        for token_start, token_end, token in token_generator:
            # there are no more words left to remove
            if all(x >= 0 for x in stemsdict.values()):
                break
            # we have already changed enough words
            if self.max_changes is not None:
                if len(transforms) >= self.max_changes:
                    break

            stem = stemmer.stem(token)

            # we ignore words that should be added
            if stemsdict.get(stem, 0) >= 0:
                continue

            # Strategy: Swap letters
            if self.mistake_type == SpellingMistakeTransformerOption.SWAP_LETTERS:
                out_strategy = self._swap_letters(token=token, stem=stem, stemmer=stemmer)
            # Strategy: Delete letter
            elif self.mistake_type == SpellingMistakeTransformerOption.DELETE_LETTER:
                out_strategy = self._delete_letter(token=token, stem=stem, stemmer=stemmer)
            # Strategy: random, choose one of both (swap or delete).
            elif self.mistake_type == SpellingMistakeTransformerOption.SWAP_OR_DELETE_RANDOMLY:
                out_strategy = self._apply_swap_or_delete(token=token, stem=stem, stemmer=stemmer)
            # Strategy: Common typos
            elif self.mistake_type == SpellingMistakeTransformerOption.COMMON_TYPOS:
                out_strategy = self._common_typo(token=token, stem=stem, stemmer=stemmer)
            # Strategy: first COMMON_TYPOS, if not possible, SWAP_OR_DELETE_RANDOMLY
            elif self.mistake_type == SpellingMistakeTransformerOption.COMMON_TYPOS_OTHERWISE_TRY_RANDOMLY_SWAP_DELETE:
                out_strategy = self._common_typo(token=token, stem=stem, stemmer=stemmer)
                if out_strategy is None:
                    out_strategy = self._apply_swap_or_delete(token=token, stem=stem, stemmer=stemmer)
            else:
                raise TransformerException("Unvalid option for spelling mistake transformer")

            if out_strategy is None:
                continue
            else:
                colored_token, new_stem = out_strategy

            # check whether the replacement changed the stem
            if stem == new_stem:
                continue

            # only if the stem has been replaced we removed the word
            transform = TransformInfo(token_start, token_end, token, stem,
                                      colored_token, new_stem)
            transforms.append(transform)

            stemsdict[stem] += 1
            feature_delta.changes[stem] = feature_delta.changes.get(
                stem, 0) - 1

        return transforms, feature_delta

    def _swap_letters(self, token: str, stem: str, stemmer) -> Optional[Tuple[str, str]]:
        """
        Strategy: Swap adjacent letters
        """

        # we should only change words that are long enough.
        if len(token) <= 4:
            return None

        # Exclude last letter.
        # If token is long enough, we can also use the whole stem and
        # swap the last letter in stem, otherwise, we need to exclude the last letter
        # in stem from being swapped.
        if len(token) >= (len(stem) + 1):
            lastletter = 0
        else:
            lastletter = 1

        # we need at least two letters in a stem (not considering first letter
        # that is excluded anyway, and maybe last letter).
        if (len(stem) - 1 - lastletter) < 2:
            return None

        indices = list(range(1, len(stem) - lastletter - 1))# -1 since swap index is the left index in the pair
        self.random.shuffle(indices)
        letter_index = indices[0]

        # modify letters in token
        prefix = token[:letter_index]
        suffix = token[letter_index + 2:]
        swapped_letters = token[letter_index + 1] + token[letter_index]
        new_token = prefix + swapped_letters + suffix
        new_stem = stemmer.stem(new_token)

        if self.debug_coloring:
            token_color = "\\debugcolor{violet}"
            swap_color = "\\debugcolor{blue}"
        else:
            token_color = ""
            swap_color = ""

        colored_swapped_letters = f"{{{swap_color}{swapped_letters}}}"
        latex_token = f"{prefix}{colored_swapped_letters}{suffix}"
        colored_token = f"{{{token_color}{latex_token}}}"

        return colored_token, new_stem

    def _delete_letter(self, token: str, stem: str, stemmer) -> Optional[Tuple[str, str]]:
        """
        Strategy: Delete letter
        """

        # Exclude last letter.
        if len(token) >= (len(stem) + 1):
            lastletter = 0
        else:
            lastletter = 1

        # we need at least one letter in a stem that can be removed
        if (len(stem) - 1 - lastletter) < 1:
            return None

        indices = list(range(1, len(stem) - lastletter))
        self.random.shuffle(indices)
        letter_index = indices[0]

        # modify letters in token
        prefix = token[:letter_index]
        suffix = token[letter_index + 1:]
        new_token = prefix + suffix
        new_stem = stemmer.stem(new_token)

        if self.debug_coloring:
            token_color = "\\debugcolor{violet}"
        else:
            token_color = ""

        latex_token = f"{prefix}{suffix}"
        colored_token = f"{{{token_color}{latex_token}}}"

        return colored_token, new_stem

    def _common_typo(self, token: str, stem: str, stemmer) -> Optional[Tuple[str, str]]:
        """
        Strategy: Use common typo
        """
        tg = TypoGenerator()
        typos = tg.gettypo(token)

        # If no matching typos found, return None.
        if len(typos) == 0:
            return None

        self.random.shuffle(typos)
        for chosen_typo in typos:
            new_token: str = chosen_typo[0]
            # if self.verbose:
            #     print(f"Trying: Word {token} -> {new_token} with method: {chosen_typo[2]}")

            new_stem = stemmer.stem(new_token)
            if new_stem != stem:
                # successful typo replacement that changes stem, and thus feature
                if self.debug_coloring:
                    token_color = "\\debugcolor{green}"
                else:
                    token_color = ""

                latex_token = f"{new_token}"
                colored_token = f"{{{token_color}{latex_token}}}"

                return colored_token, new_stem

        return None


    @classmethod
    def _enable_spellingmistakes(cls, doc, debug_coloring=False):
        default_insert = cls._find_last_documentclass(doc)
        transforms = []

        if debug_coloring:
            if (t := cls._enable_debug_coloring(doc,
                                                default_insert)) is not None:
                transforms.append(t)

        return cls._apply_transforms(doc, transforms)
