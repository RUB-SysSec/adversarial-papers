import copy
import typing

from utils.pdf_utils import get_stop_words
from utils.attack_utils import clean_dict, add_words_padding, add_words_stop_words_padding
from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.ReplacementTransform import (
    TransformInfo)
from problemspace.transformers.CommentBoxTransformer import CommentBoxTransformer
from problemspace.exceptions.TransformerException import TransformerException
from problemspace.transformers.FeatureDelta import FeatureDelta


class CommentBoxAddWordTransformer(CommentBoxTransformer):
    """
    Feature Addition (can also be used to remove a word during addition, see below).
    Adds a comment box. In this comment box, words are placed that are extracted by pdftotext, but are not visible.

    To be able to add a text box, we need to sacrifice a word in the text (that is no longer parsed
    by pdftotext). The scope of the word should be limited: After abstract until Bibliography (excl.) only.

    We have the following order:
    A. Check if some feature must be decreased, if so, try to find that feature in text so that we can replace it.
        This is a good idea if we have to remove another feature anyway.
    B. If not or not possible, try to find stop word so that no impact by replacement.
    C. If not or not possible, try to find word that has no large impact on feature vector [not implemented, yet]
    D. If not or not possible, choose word randomly. -> side effect. [not implemented, yet]
    C & D are currently not implemented, as we should actually find a stop word always (e.g., 'is' is a stop word).
    """

    def __init__(self,
                 logsettings: LogSettings,
                 ignored_environments=[],
                 *args,
                 **kwargs):
        super().__init__(logsettings=logsettings,
                         ignored_environments=ignored_environments,
                         *args,
                         **kwargs)

    # @Overwrite
    def _transform_main_part(self, doc: str, current_wordsdict: dict):
        transforms = []
        featuredelta = FeatureDelta()
        # current_wordsdict = copy.deepcopy(current_wordsdict) # no need, as copied in clean_dict()

        # A. Preprocessing
        # It seems we can only add ascii characters in a box,
        # so let's remove any words in wordsdict that could cause problems
        current_wordsdict, cleaned_features = clean_dict(requested_changes=current_wordsdict,
                   logger=self.logger, max_ord_value=128)

        # B. try to find word that needs to be decreased in text
        # can_del_word: bool = len([1 for v in  transformationstate.current_wordsdict.values() if v < 0]) > 0
        can_del_word: bool = any(x < 0 for x in current_wordsdict.values())
        if can_del_word:
            transforms, featuredelta = self._replace_deletion_words(doc=doc, current_wordsdict=current_wordsdict)

        # C. If no words to be decreased or not possible, find stop words
        if len(transforms) == 0:
            transforms, featuredelta = self._replace_stop_words(doc=doc, current_wordsdict=current_wordsdict)

        # D. Find words with little impact on feature vector.
        #   Not implemented, yet. Actually, we should find stop words easily.
        # E. Use random word.
        #   Not implemented, yet. Actually, we should find stop words easily.

        # F. Problems? Actually, we should always be able to add a box, so let's raise an exception.
        # But we do not have to, we just do that here as signal for unexcepted behaviour.
        if len(transforms) == 0:
            raise TransformerException("Could not find word to replace for comment box transformer")

        # E. Get generic restrictions
        blockedfeatures: set = self._get_problemspace_constraints(doc=doc, wordsdict=current_wordsdict)
        featuredelta.unrealizable_words.update(blockedfeatures)

        return featuredelta, transforms

    def _replace_deletion_words(self, doc: str, current_wordsdict: dict):
        tokenizer = self._build_tokenizer()
        stemmer = self._build_stemmer()
        transforms = []
        stemsdict = current_wordsdict  # no copy necessary here

        feature_delta: FeatureDelta = FeatureDelta()

        # Iterate over document and its tokens
        for token_start, token_end, token in \
                self._iterate_over_document(doc=doc, tokenizer=tokenizer, check_within_cmd=True):
            stem = stemmer.stem(token)

            # we ignore words that should be added
            if stemsdict.get(stem, 0) >= 0:
                continue

            # we add something; we simply overwrite feature-delta here, since we only add something once.
            # The feature-delta here contains the words that are added, the removals are considered below.
            stringtoadd, feature_delta = self.convert_words_dict(
                wordsdict=current_wordsdict, stemmer=stemmer)

            if self.debug_coloring:
                token_color = "\\debugcolor{purple}"
            else:
                token_color = ""
            commentbox: str = self._get_commentbox_command(stringtoadd=stringtoadd, replacedstring=token)
            colored_token = f"{{{token_color}{commentbox}}}"

            transform = TransformInfo(token_start=token_start, token_end=token_end, token=token, stem=stem,
                                      new_token=colored_token, new_stem=stem)
            transforms.append(transform)
            feature_delta.changes[stem] = feature_delta.changes.get(
                stem, 0) - 1 # here we add the removals in feature-delta

            break  # we only add one commentbox

        return transforms, feature_delta

    def _replace_stop_words(self, doc: str, current_wordsdict: dict):
        tokenizer = self._build_tokenizer()
        stemmer = self._build_stemmer()
        transforms = []
        stop_words = get_stop_words()

        feature_delta: FeatureDelta = FeatureDelta()

        # Iterate over document and its tokens
        for token_start, token_end, token in \
                self._iterate_over_document(doc=doc, tokenizer=tokenizer, check_within_cmd=True):
            if token in stop_words:

                stringtoadd, feature_delta = self.convert_words_dict(
                    wordsdict=current_wordsdict, stemmer=stemmer)

                if self.debug_coloring:
                    token_color = "\\debugcolor{purple}"
                else:
                    token_color = ""

                commentbox: str = self._get_commentbox_command(stringtoadd=stringtoadd, replacedstring=token)
                colored_token = f"{{{token_color}{commentbox}}}"

                transform = TransformInfo(token_start=token_start, token_end=token_end, token=token, stem="",
                                          new_token=colored_token, new_stem="")
                transforms.append(transform)

                break  # we only add one commentbox

        return transforms, feature_delta

    def convert_words_dict(self, wordsdict: typing.Dict[str, int], stemmer) -> typing.Tuple[str, FeatureDelta]:
        """
        Creates words string for the passed dict;
        For instance, dict{'hello': 2, 'world': 1} leads to string with "hello hello world".
        :return new string, dict with increased feature values
        """
        words_addition: str = ""
        delta: FeatureDelta = FeatureDelta()
        for k, v in wordsdict.items():
            if v > 0:

                stemable_word: typing.Optional[str] = add_words_padding(requested_word=k, stemmer=stemmer,
                                                                        logger=self.logger)
                if stemable_word is None:
                    continue

                addable_word: typing.Optional[str] = add_words_stop_words_padding(requested_word=stemable_word,
                                                                                   stemmer=stemmer, logger=self.logger)
                if addable_word is None:
                    continue

                # if we had to add a stem in both cases, this will create a conflict
                if (stemable_word != k) and (addable_word != stemable_word):
                    self.logger.debug(f"        -> ProblemSpace: Converts-Words-Dict {stemable_word} vs. {addable_word}")
                    continue

                words_addition += (addable_word + " ") * v
                delta[k] = v

        return words_addition, delta
