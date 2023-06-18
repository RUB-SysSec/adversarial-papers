import random
import re
from copy import copy
from typing import List, Optional, Tuple

import homoglyphs as hg
from problemspace.transformers.FeatureDelta import FeatureDelta
from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.ReplacementTransform import (
    ReplacementTransformer, TransformInfo)
from problemspace.transformers.TransformationState import TransformationState


class HomoglyphTransformer(ReplacementTransformer):
    """
    Changes a word by replacing a single character by its homoglyph.
    Allows us to remove features.
    """
    def __init__(self,
                 logsettings: LogSettings,
                 replacements=None,
                 seed=42,
                 ignored_environments=[],
                 *args,
                 **kwargs):

        super().__init__(logsettings=logsettings,
                         ignored_environments=ignored_environments,
                         *args,
                         **kwargs)
        self.replacements = replacements
        self.random = random.Random(seed)

    def _transform(self,
                   transformationstate: TransformationState) -> FeatureDelta:
        tokenizer = self._build_tokenizer()
        stemmer = self._build_stemmer()
        replacements = self._build_replacements()

        # read main doc
        doc = transformationstate.pdflatexsource.get_main_document()

        # enable latex compilation for homoglyphs
        doc = self._enable_homoglyphs(doc, debug_coloring=self.debug_coloring)

        # find transforms
        # i.e. an "index of character in document" to "homoglyph" mapping
        transforms, featuredelta = self._find_transforms(
            doc,
            transformationstate.current_wordsdict,
            stemmer=stemmer,
            tokenizer=tokenizer,
            replacements=replacements)

        # apply transforms
        doc = self._apply_transforms(doc, transforms)

        # save main doc
        transformationstate.pdflatexsource.save_latex(doc)

        # return the wordsdict delta
        return featuredelta

    def _find_transforms(
            self, doc, wordsdict, stemmer, tokenizer,
            replacements) -> Tuple[List[TransformInfo], FeatureDelta]:
        # copy wordsdict and make sure that we operate on the word stems
        stemsdict = copy(wordsdict)

        feature_delta: FeatureDelta = FeatureDelta()

        # get generic restrictions
        blockedfeatures: set = self._get_problemspace_constraints(doc=doc, wordsdict=wordsdict)
        feature_delta.unrealizable_words.update(blockedfeatures)

        transforms = []

        token_generator = self._iterate_over_document(
            doc=doc,
            tokenizer=tokenizer,
            check_within_cmd=True)

        # Iterate over document and its tokens
        for token_start, token_end, token in token_generator:
            # there are no more words left to remove
            if all(x >= 0 for x in stemsdict.values()):
                break

            stem = stemmer.stem(token)

            # homoglyph replacement "removes" a word from the document; thus,
            # we ignore words that should be added
            if stemsdict.get(stem, 0) >= 0:
                continue

            # we do not want to replace the first letter in each word but
            # rather use a random index
            indices = list(range(len(stem)))
            self.random.shuffle(indices)

            # try to replace a letter at a random index until we succeed or
            # run out of indices
            for letter_index in indices:
                letter = token[letter_index]
                valid_homoglyphs = replacements.get(letter)

                # we found no homoglyph for this letter
                if valid_homoglyphs is None:
                    continue

                # Right now, we just choose one valid homoglyph in a fixed way. Can be improved.
                homoglyph = valid_homoglyphs[-1]

                # replace homoglyph in token
                prefix = token[:letter_index]
                suffix = token[letter_index + 1:]
                new_token = prefix + homoglyph + suffix
                new_stem = stemmer.stem(new_token)

                if self.debug_coloring:
                    token_color = "\\debugcolor{red}"
                    homoglyph_color = "\\debugcolor{blue}"
                else:
                    token_color = ""
                    homoglyph_color = ""

                colored_homoglyph = f"{{{homoglyph_color}{homoglyph}}}"
                latex_token = f"{prefix}{colored_homoglyph}{suffix}"

                encoding = "\\fontencoding{T2A}\\selectfont"
                colored_token = f"{{{token_color}{encoding} {latex_token}}}"

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

                break

        return transforms, feature_delta

    @classmethod
    def _enable_homoglyphs(cls, doc, debug_coloring=False):
        default_insert = cls._find_last_documentclass(doc)
        transforms = []

        # Font encoding must be added before babel
        if (t := cls._add_fontenc(doc, default_insert)) is not None:
            transforms.append(t)

        if (t := cls._add_inputenc(doc, default_insert)) is not None:
            transforms.append(t)

        if (t := cls._add_russian_babel(doc, default_insert)) is not None:
            transforms.append(t)

        if debug_coloring:
            if (t := cls._enable_debug_coloring(doc,
                                                default_insert)) is not None:
                transforms.append(t)

        return cls._apply_transforms(doc, transforms)

    @staticmethod
    def _add_russian_babel(doc, default_insert) -> Optional[TransformInfo]:
        usepackage_russian = "\\usepackage[russian,english]{babel}\n"

        if (m := re.search(r"\\usepackage(\[.*?\])?{babel}", doc)) is not None:
            start, end = m.span()
            original = m.group(0)
            parameters = m.group(1)

            if "[russian]" == parameters:
                return None

            # \usepackage{babel}
            if len(parameters) == 0:
                return TransformInfo(start, end, original, original,
                                     usepackage_russian, usepackage_russian)

            # \usepackage[]{babel}
            # \usepackage[somelang]{babel}
            # \usepackage[somelang,someother,...]{babel}
            else:
                languages = parameters[1:-1].split(",")
                assert len(languages) > 0

                if "russian" in languages:
                    return None

                # Add russian as the first language as to not overwrite
                # the existing language configuration (i.e. last entry)
                languages.insert(0, "russian")

                babel = "\\usepackage[" + ",".join(languages) + "]{babel}\n"

                return TransformInfo(start, end, original, original, babel,
                                     babel)
        else:
            return TransformInfo(default_insert, default_insert, "", "",
                                 usepackage_russian, usepackage_russian)

    @staticmethod
    def _add_inputenc(doc, default_insert) -> Optional[TransformInfo]:
        replacement = "\\usepackage[utf8]{inputenc}\n"

        if (m := re.search(r"\\usepackage(\[.*\]){inputenc}",
                           doc)) is not None:
            original = m.group(0)

            if original == replacement:
                return None

            return TransformInfo(m.start(), m.end(), original, original,
                                 replacement, replacement)
        else:
            return TransformInfo(default_insert, default_insert, "", "",
                                 replacement, replacement)

    @staticmethod
    def _add_fontenc(doc, default_insert) -> Optional[TransformInfo]:
        replacement = "\\usepackage[T2A,OT1]{fontenc}\n"

        if (m := re.search(r"\\usepackage(\[.*\])?{fontenc}",
                           doc)) is not None:
            original = m.group(0)
            parameters = m.group(1)

            # \usepackage{fontenc}
            if len(parameters) == 0:
                return TransformInfo(m.start(), m.end(), original, original,
                                     replacement, replacement)

            # \usepackage[]{fontenc}
            # \usepackage[somelang]{fontenc}
            # \usepackage[somelang,someother,...]{fontenc}
            else:
                # remove parentheses
                parameters = parameters[1:-1]

                if len(parameters) == 0:
                    encodings = []
                else:
                    encodings = parameters.split(",")

                if "T2A" in encodings:
                    return None

                # if (for some reason) we receive \usepackage[]{fontenc} the
                # default encoding is still OT1 (and must not be changed to
                # T2A)
                if len(encodings) == 0:
                    encodings.append("OT1")

                # add T2A-encoding at the start of the list as not to overwrite
                # the default encoding (i.e. last entry)
                encodings.insert(0, "T2A")

                replacement = "\\usepackage[" + ",".join(
                    encodings) + "]{fontenc}"

                return TransformInfo(m.start(), m.end(), original, original,
                                     replacement, replacement)
        else:
            return TransformInfo(default_insert, default_insert, "", "",
                                 replacement, replacement)

    def _build_replacements(self):
        if self.replacements is not None:
            return self.replacements

        homoglyphs = hg.Homoglyphs(languages={'ru', 'en'})
        replacements = {}

        for letter in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
            hgs = homoglyphs.get_combinations(letter)
            hgs = [h for h in hgs if h != letter]

            if len(hgs) > 0:
                replacements[letter] = hgs

        # TODO: Remove letters that do not fit in
        del replacements["l"]
        del replacements["r"]

        return replacements
