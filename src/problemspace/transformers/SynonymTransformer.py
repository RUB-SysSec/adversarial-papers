import random
from pathlib import Path
from copy import copy
from typing import List, Tuple, Optional
import spacy

import gensim
from problemspace.misc.synonyms.synonyms import gen_synonyms
from problemspace.transformers.FeatureDelta import FeatureDelta
from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.ReplacementTransform import (
    ReplacementTransformer, TransformInfo)
from problemspace.transformers.TransformationState import TransformationState


class SynonymTransformer(ReplacementTransformer):
    """
    Replaces words in the text by their synonym. Uses a pre-trained synonym model.
    Allows us to remove features.
    """
    def __init__(self,
                 logsettings: LogSettings,
                 synonym_model_path: Optional[Path]=None,
                 synonym_threshold=0.9,
                 max_changes=None,
                 seed=42,
                 pos_checker: int = 0,
                 ignored_environments=[],
                 *args,
                 **kwargs):
        """
        Inits synonym transformer.
        :param logsettings: settings for logging.
        :param synonym_model_path: path to synonym model, if None, default model will be used.
        :param synonym_threshold: threshold for synonym model
        :param max_changes: maximum number of changed words
        :param seed: seed for randomness
        :param pos_checker: integer specifying level of checking. 0 = no checking, 1 = basic checking, 2 = strict checking.
        :param ignored_environments: ignored environments.
        :param args: further args
        :param kwargs: further args
        """
        super().__init__(logsettings=logsettings,
                         ignored_environments=ignored_environments,
                         *args,
                         **kwargs)
        self.synonym_model_path = synonym_model_path
        self.synonym_threshold = synonym_threshold
        self.random = random.Random(seed)
        self.max_changes = max_changes
        self.pos_checker: int = pos_checker
        self.nlp = None
        if self.pos_checker > 0:
            self.nlp = spacy.load("en_core_web_sm")

    def _transform(self,
                   transformationstate: TransformationState) -> FeatureDelta:
        tokenizer = self._build_tokenizer()
        stemmer = self._build_stemmer()
        synonym_model = self._build_synonym_model()

        # read main doc
        doc = transformationstate.pdflatexsource.get_main_document()

        # enable color for debug coloring
        doc = self._enable_synonym_coloring(doc, debug_coloring=self.debug_coloring)

        # find transformations (replace word with synonym)
        transforms, featuredelta = self._find_transforms(
            doc,
            transformationstate.current_wordsdict,
            stemmer=stemmer,
            tokenizer=tokenizer,
            synonym_model=synonym_model)

        # apply transforms
        doc = self._apply_transforms(doc, transforms)

        # save main doc
        transformationstate.pdflatexsource.save_latex(doc)

        # return the wordsdict delta
        return featuredelta

    def _find_transforms(
            self, doc, wordsdict, stemmer, tokenizer,
            synonym_model) -> Tuple[List[TransformInfo], FeatureDelta]:
        # copy wordsdict and make sure that we operate on the word stems
        stemsdict = copy(wordsdict)

        feature_delta: FeatureDelta = FeatureDelta()

        # get generic restrictions
        blockedfeatures: set = self._get_problemspace_constraints(doc=doc, wordsdict=wordsdict)
        feature_delta.unrealizable_words.update(blockedfeatures)

        transforms = []

        content_start = doc.index("\\begin{document}")
        content_end = doc.index("\\end{document}")
        assert content_start <= content_end

        token_list = list(
            self._iterate_over_document(
                doc=doc,
                tokenizer=tokenizer,
                check_within_cmd=True))
        tokens = set(token for _, _, token in token_list)

        synonym_dict = gen_synonyms(synonym_model,
                                    tokens,
                                    threshold=self.synonym_threshold)

        for token_start, token_end, token in token_list:
            # there are no more words left to add / remove
            if all(x == 0 for x in stemsdict.values()):
                break
            # we have already changed enough words
            if self.max_changes is not None:
                if len(transforms) >= self.max_changes:
                    break

            # find synonyms for token
            synonyms = synonym_dict.get(token, [])
            if len(synonyms) == 0:
                continue

            stem = stemmer.stem(token)

            transform = self._try_adding_word_using_synonym(
                token_start, token_end, token, stem, stemmer, stemsdict,
                synonyms, feature_delta, doc)

            if transform is not None:
                transforms.append(transform)
                continue

            transform = self._try_deleting_word_using_synonym(
                token_start, token_end, token, stem, stemmer, stemsdict,
                synonyms, feature_delta, doc)

            if transform is not None:
                transforms.append(transform)

        return transforms, feature_delta

    def _try_adding_word_using_synonym(self, token_start, token_end, token,
                                       stem, stemmer, stemsdict, synonyms,
                                       feature_delta, doc):
        for synonym in synonyms:
            synonym_stem = stemmer.stem(synonym)

            if stemsdict.get(synonym_stem, 0) > 0:
                if self._pos_checking(token_start=token_start, token_end=token_end,
                                      token=token, new_token=synonym, doc=doc, mode="ADD") is True:
                    stemsdict[synonym_stem] -= 1
                    feature_delta.changes[
                        synonym_stem] = feature_delta.changes.get(synonym_stem,
                                                                  0) + 1

                    if self.debug_coloring:
                        token_color = "\\debugcolor{magenta}"
                        colored_token = f"{{{token_color}{synonym}}}"
                    else:
                        colored_token = synonym

                    return TransformInfo(token_start, token_end, token, stem,
                                         colored_token, synonym_stem)

    def _try_deleting_word_using_synonym(self, token_start, token_end, token,
                                         stem, stemmer, stemsdict, synonyms,
                                         feature_delta, doc):
        # synonym replacement "removes" a word from the document; thus,
        # we ignore words that should be added
        if stemsdict.get(stem, 0) >= 0:
            return

        # We try all possible synonyms in random order.
        shuffled_synonyms = self.random.sample(synonyms, len(synonyms)) # not in-place here!
        for new_token in shuffled_synonyms:
            # synonym chosen, now get stem
            new_stem = stemmer.stem(new_token)

            # the synonym's stem must be different from the token's
            # stem to have an effect on the feature space
            if new_stem == stem:
                continue

            # Use part-of-speech tagging, check that same tags, i.e., synonym has same tag
            # Example: adversary -> synonyms: {attackers, attacker}. Adversary and attacker have same "NN" tag.
            if self._pos_checking(token_start=token_start, token_end=token_end, token=token,
                                  new_token=new_token, doc=doc, mode="DEL") is False:
                continue

            stemsdict[stem] += 1
            feature_delta.changes[stem] = feature_delta.changes.get(stem, 0) - 1

            if self.debug_coloring:
                token_color = "\\debugcolor{olive}"
                colored_token = f"{{{token_color}{new_token}}}"
            else:
                colored_token = new_token

            return TransformInfo(token_start, token_end, token, stem, colored_token,
                                 new_stem)
        return

    def _build_synonym_model(self):
        if self.synonym_model_path is None:
            path = Path.home().joinpath('adversarial-papers/evaluation/problemspace/synonyms/committees_full-nostem.w2v.gz')  # sec-conf-paper-nostem.w2v.gz"
            return gensim.models.Word2Vec.load(str(path))
        else:
            path = self.synonym_model_path
            return gensim.models.Word2Vec.load(str(path))

    def _pos_checking(self, token_start, token_end, token, new_token, doc, mode) -> bool:
        """
        POS checking
        :return: true if all right, false if continue
        """
        if self.pos_checker == 0:
            # no checking
            return True
        else:

            # Actually, we would need split the text into sentences. However, getting the tokens is already
            # challenging. So we use here a simple strategy. We extract the text before and after the 'token'
            # which is hopefully enough to get a more accurate POS tag for the synonym and token.
            eps = 20
            text_of_interest = doc[max(0, token_start-eps) : (token_end+eps)]
            text_of_interest_2 = text_of_interest[:eps] + new_token + text_of_interest[(-eps):]
            token_tag = None
            new_token_tag = None
            for outcome in self.nlp(text_of_interest):
                if outcome.idx == eps:
                    token_tag = outcome.tag_
                    break
            for outcome in self.nlp(text_of_interest_2):
                if outcome.idx == eps:
                    new_token_tag = outcome.tag_
                    break

            if token_tag is None or new_token_tag is None:
                self.printlogdebug(f"Prob-Space-Synonym-Error!") # should not happen actually!
            if token_tag is None:
                token_tag = self.nlp(token)[0].tag_
            if new_token_tag is None:
                new_token_tag = self.nlp(new_token)[0].tag_

            if self.pos_checker == 1:
                # just a basic check with some exceptions
                if token_tag == "NN":
                    if new_token_tag not in ["NN", "JJ", "RB", "VBG", "VB", "VBN"]:
                        self.printlogdebug(
                            f"Prob-Space-Synonym-Basic-NN-Mismatch: {mode}: {token} has {token_tag} but {new_token} has {new_token_tag}")
                        return False
                else:
                    if new_token_tag != token_tag:
                        self.printlogdebug(
                            f"Prob-Space-Synonym-Basic-NonNN-Mismatch: {mode}: {token} has {token_tag} but {new_token} has {new_token_tag}")
                        return False

                self.printlogdebug(
                    f"Prob-Space-Synonym-Basic-Success: {mode}: {token}, {new_token} have {token_tag}")
                return True

            elif self.pos_checker == 2:
                # strict checking
                if token_tag != new_token_tag:
                    self.printlogdebug(
                        f"Prob-Space-Synonym-Strict-Mismatch: {mode}: {token} has {token_tag} but {new_token} has {new_token_tag}")
                    return False
                else:
                    self.printlogdebug(
                        f"Prob-Space-Synonym-Strict-Success: {mode}: {token}, {new_token} have {token_tag}")
                    return True

            elif self.pos_checker > 2:
                raise NotImplementedError()

            self.printlogdebug(
                f"Prob-Space-Synonym-Success: {mode}: {token}, {new_token} have {token_tag}")
            return True

    @classmethod
    def _enable_synonym_coloring(cls, doc, debug_coloring=False):
        if debug_coloring:
            default_insert = cls._find_last_documentclass(doc)
            transforms = []

            if (t := cls._enable_debug_coloring(doc, default_insert)) is not None:
                transforms.append(t)

            return cls._apply_transforms(doc, transforms)
        else:
            return doc