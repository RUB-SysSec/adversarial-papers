import typing
from abc import abstractmethod

from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.ReplacementTransform import (
    ReplacementTransformer, TransformInfo)
from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.FeatureDelta import FeatureDelta


class CommentBoxTransformer(ReplacementTransformer):
    """
    This transformeer uses a comment box to add / remove features, provided by latex package accsupp.
    To this end, we need to add the latex package accsupp (if not loaded already), and then add the text box.
    Two variants exist: see CommentBoxAddWordTransformer, and CommentBoxDelWordTransformer.

    Some Notes:
    a. This transformer finds the locations by using regex. This is very fast. A more robust approach would
    be to use a latex parser, but parsing the document requires more time (and some parsers did not work for some
    submissions from the dataset).

    b. If a word is already used by a comment-box, it won't be used twice. This is due to the tokenizer, that
    does not get the word within the commentbox (the replaced word becomes <word>\\endaccsup).

    TODO implement that only until bibliography!
    TODO shuffle replacement locations in paper
    """

    def __init__(self,
                 logsettings: LogSettings,
                 ignored_environments,
                 *args,
                 **kwargs):
        super().__init__(logsettings=logsettings,
                         ignored_environments=ignored_environments,
                         *args,
                         **kwargs)

    # @Overwritten
    def _transform(self, transformationstate: TransformationState) -> FeatureDelta:

        doc = transformationstate.pdflatexsource.get_main_document()
        current_wordsdict = transformationstate.current_wordsdict

        # Create package include if necessary
        doc = self._enable_commentbox(doc, debug_coloring=self.debug_coloring)

        # get all transformations
        featuredelta, transforms = self._transform_main_part(doc=doc, current_wordsdict=current_wordsdict)

        # apply transforms
        doc = self._apply_transforms(doc, transforms)

        # save main doc
        transformationstate.pdflatexsource.save_latex(doc)

        # return the wordsdict delta
        return featuredelta

    @abstractmethod
    def _transform_main_part(self, doc: str, current_wordsdict: dict) -> typing.Tuple[
        FeatureDelta, typing.List[TransformInfo]]:
        """
        Main part of comment box transformer. Needs to be implemented.
        :param doc: main document
        :param current_wordsdict: word dict with changes
        :return: feature delta and list of transformations to be applied on document.
        """
        pass

    @classmethod
    def _enable_commentbox(cls, doc, debug_coloring=False):
        default_insert = cls._find_last_documentclass(doc)
        transforms = []

        if (t := cls._add_accsupp(doc, default_insert)) is not None:
            transforms.append(t)

        if debug_coloring:
            if (t := cls._enable_debug_coloring(doc=doc, default_insert_pos=default_insert)) is not None:
                transforms.append(t)

        return cls._apply_transforms(doc, transforms)

    @staticmethod
    def _add_accsupp(doc, default_insert) -> typing.Optional[TransformInfo]:
        neededpackage: str = "\\usepackage{accsupp}\n"
        if "usepackage{accsupp}" not in doc:
            return TransformInfo(default_insert, default_insert, "", "",
                                 neededpackage, neededpackage)
        else:
            return None

    @staticmethod
    def _get_commentbox_command(stringtoadd: str, replacedstring: str):
        """
        Creates comment box command in latex.
        :param stringtoadd: string that will be added in commentbox (extracted by pdftotext, but not visible),
        can consists of multiple words that need to be added. See convert_words_dict method.
        :param replacedstring: word where the comment box is attached to (not visible)
        :return: comment box latex command
        """
        commentbox: str = "".join(["\\BeginAccSupp{ActualText=", stringtoadd, "}",
                                   replacedstring + "\\EndAccSupp{}"])
        return commentbox
