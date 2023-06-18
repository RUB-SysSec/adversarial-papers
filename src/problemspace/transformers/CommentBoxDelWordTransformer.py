from copy import copy

from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.CommentBoxTransformer import CommentBoxTransformer
from problemspace.transformers.FeatureDelta import FeatureDelta
from problemspace.transformers.ReplacementTransform import (
    TransformInfo)


class CommentBoxDelWordTransformer(CommentBoxTransformer):
    """
    Feature Removal Only.
    Puts an empty comment box onto a word, just to remove it from pdftotest.
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

        # A. Only necessary if there is a word that we should remove
        can_del_word: bool = any(x < 0 for x in current_wordsdict.values())
        if can_del_word:
            transforms, featuredelta = self._replace_deletion_words(doc=doc, current_wordsdict=current_wordsdict)

        # B. Get generic restrictions
        blockedfeatures: set = self._get_problemspace_constraints(doc=doc, wordsdict=current_wordsdict)
        featuredelta.unrealizable_words.update(blockedfeatures)

        return featuredelta, transforms


    def _replace_deletion_words(self, doc: str, current_wordsdict: dict):
        # Difference to CommentBoxAddWordTransformer's replace_deleteion_words:
        #   a. we do not add any word in commentbox.
        #   b. we do not only add one commentbox, but one box for each removed word.
        #   c. different debug color.

        tokenizer = self._build_tokenizer()
        stemmer = self._build_stemmer()
        transforms = []
        stemsdict = copy(current_wordsdict)

        feature_delta: FeatureDelta = FeatureDelta()
        stringtoadd = "is" # this transformer only adds 'stop word' which is not parsed.

        # Iterate over document and its tokens
        for token_start, token_end, token in \
                self._iterate_over_document(doc=doc, tokenizer=tokenizer, check_within_cmd=True):

            # there are no more words left to remove
            if all(x >= 0 for x in stemsdict.values()):
                break

            stem = stemmer.stem(token)

            # we ignore words that should be added
            if stemsdict.get(stem, 0) >= 0:
                continue

            if self.debug_coloring:
                token_color = "\\debugcolor{cyan}"
            else:
                token_color = ""
            commentbox: str = self._get_commentbox_command(stringtoadd=stringtoadd, replacedstring=token)
            colored_token = f"{{{token_color}{commentbox}}}"

            transform = TransformInfo(token_start=token_start, token_end=token_end, token=token, stem=stem,
                                      new_token=colored_token, new_stem=stem)
            transforms.append(transform)

            stemsdict[stem] += 1
            feature_delta.changes[stem] = feature_delta.changes.get(
                stem, 0) - 1


        return transforms, feature_delta