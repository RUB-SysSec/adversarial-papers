from abc import abstractmethod
from typing import List, Optional

from nltk.stem import PorterStemmer
from nltk.tokenize import TreebankWordTokenizer, WhitespaceTokenizer
from problemspace.exceptions.TransformerException import TransformerException
from problemspace.transformers.FeatureDelta import FeatureDelta
from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.Transformer import Transformer
from problemspace.transformers.ReplacementTransform import ReplacementTransformer


class SentenceTransformer(ReplacementTransformer):

    def __init__(self, logsettings: LogSettings, stemmer=None, ignored_environments=[]):
        super().__init__(logsettings=logsettings, stemmer=stemmer, ignored_environments=ignored_environments)

    @abstractmethod
    def _transform(self,
                   transformationstate: TransformationState) -> FeatureDelta:
        pass

    @classmethod
    def _enable_sentence_coloring(cls, doc, debug_coloring=False):
        if debug_coloring:
            default_insert = cls._find_last_documentclass(doc)
            transforms = []

            if (t := cls._enable_debug_coloring(doc, default_insert)) is not None:
                transforms.append(t)

            return cls._apply_transforms(doc, transforms)
        else:
            return doc

    def _make_colorized_text(self, text: str) -> str:
        if self.debug_coloring:
            text_color = "\\debugcolor{brown}"
            colored_text = f"{{{text_color}{text}}}"
        else:
            colored_text = text

        return colored_text