import copy
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TRANSFORMERS_VERBOSITY'] = 'critical'

from abc import abstractmethod
import pickle
from pathlib import Path
import random
from typing import List, Optional, Tuple, Dict, Set
import spacy
import re

from problemspace.transformers.SentenceTransformer.SentenceTransformer import SentenceTransformer
from problemspace.transformers.FeatureDelta import FeatureDelta
from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.TransformationState import TransformationState


class LangModelTransformer(SentenceTransformer):
    """
    Creates sentences with words-to-be-added based on a language model like GPT-2.
    """

    def __init__(self,
                 logsettings: LogSettings,
                 seed=11,
                 stemming_mapping_path: Optional[Path] = None,
                 max_words=None,
                 ignored_environments=[]):

        super().__init__(logsettings=logsettings, ignored_environments=ignored_environments)
        self.max_words = max_words
        self.seed = seed

        self.nlp = spacy.load("en_core_web_sm")

        # How many sentences should be generated for each word that needs to be added:
        self.max_sentences_per_word_addition = 2

        self.random = random.Random(self.seed)

        self.maps_stemming: List[Dict[str, Set[str]]] = self._load_stemming_mapping(
            stemming_mapping_path=stemming_mapping_path)


    @staticmethod
    def _load_stemming_mapping(stemming_mapping_path: Optional[Path]) -> List[Dict[str, Set[str]]]:
        """
        Load the map that defines a mapping from each stem to possible unstemmed words.
        :return: list of mappings.
        """
        if stemming_mapping_path is None:
            basis_path = Path("problemspace/misc/stemming_mapping/")
        else:
            basis_path = stemming_mapping_path

        maps_stemming: List[Dict[str, Set[str]]] = []

        # Define models (first model has higher priority, words from mapping are preferred)
        # model 1 from pdf paper corpus
        path1 = Path(basis_path / "map_stemming_reverted_tpms_corpus.pkl")
        assert path1.exists(), "map_stemming_reverted_tpms_corpus.pkl not found"

        # model 2 from English dictionary
        path2 = Path(basis_path / "map_stemming_reverted.pkl")
        assert path2.exists(), "map_stemming_reverted.pkl not found"

        for curpath in [path1, path2]:
            with open(curpath, 'rb') as f:
                cur_map_stemming = pickle.load(f)
                maps_stemming.append(cur_map_stemming)

        return maps_stemming

    def _get_word_for_stemmed_word(self, stemmed_word: str) -> Optional[str]:
        """
        Get unstemmed word for stemmed word, or None if nothing found
        """

        for map_stemming in self.maps_stemming:
            if stemmed_word in map_stemming:
                possible_words = map_stemming[stemmed_word]
                x = list(possible_words)
                x.sort() # this is necessary, because we have a set and thus order of list may differ...
                return self.random.choice(x)
        return None

    # @Overwrite
    def _transform(self, transformationstate: TransformationState) -> FeatureDelta:

        doc = transformationstate.pdflatexsource.get_main_document()
        current_wordsdict = copy.copy(transformationstate.current_wordsdict)

        # enable color for debug coloring
        doc = self._enable_sentence_coloring(doc, debug_coloring=self.debug_coloring)
        docl = doc.lower()

        # get position to add sentences, if no position found, we stop.
        insertion_position: Optional[int] = self._get_insertion_position(docl = docl)
        if insertion_position is None:
            return FeatureDelta()

        # get all transformations
        featuredelta, transforms_sentences = self._transform_main_part(current_wordsdict=current_wordsdict,
                                                                       doc=doc,
                                                                       insertion_position=insertion_position)
        if len(featuredelta.changes) == 0:
            return FeatureDelta()

        # apply transforms, for sake of simplicity, we do not use TransformInfo here
        doc = self._apply_transforms_sentences(doc=doc, transforms_sentences=transforms_sentences,
                                     insertion_position=insertion_position)

        # save main doc
        transformationstate.pdflatexsource.save_latex(doc)

        # get generic restrictions
        blockedfeatures: set = self._get_problemspace_constraints(doc=doc, wordsdict=current_wordsdict)
        featuredelta.unrealizable_words.update(blockedfeatures)

        # return the wordsdict delta
        return featuredelta

    @abstractmethod
    def _transform_main_part(self,
                             current_wordsdict: dict,
                             doc: str,
                             insertion_position: int) -> Tuple[FeatureDelta, List[Tuple[str, str]]]:
        """
        Creates the sentences for each word that needs to be added
        :param current_wordsdict: requested words to be added
        :param doc: current paper
        :insertion_position: location where we will add generated text
        :return: feature-delta & list of tuple where each tuple contains word and possible sentence(s) to add that word
        """
        pass

    def _find_related_work(self, docl: str) -> Optional[int]:
        m = re.search(r"section{(\w|\s)*(related work)(\w|\s)*}", docl)
        if m is None:
            self.printlogerr("ProblemSpace: GPT2. No related work section found")
            return None
        else:
            return m.end()

    def _find_discussion(self, docl: str) -> Optional[int]:
        m = re.search(r"section{(\w|\s)*(discussion)(\w|\s)*}", docl)
        if m is None:
            self.printlogerr("ProblemSpace: GPT2. No discussion section found")
            return None
        else:
            return m.end()

    def _get_insertion_position(self, docl: str) -> Optional[int]:

        m_end = self._find_related_work(docl = docl)
        if m_end is None:
            # 1911.05673 has no related work in our dataset, in this case, let's try Discussion
            m_end = self._find_discussion(docl=docl)
            if m_end is None:
                return None

        # find next section to insert text between related work and next section
        mx = re.search(r"\\section{", docl[m_end:])
        if mx is None:
            self.printlogerr("ProblemSpace: GPT2. No section after related work found")
            return None

        next_section_start = m_end + mx.start()
        return next_section_start

    def _apply_transforms_sentences(self, doc: str,
                          transforms_sentences: List[Tuple[str, str]],
                          insertion_position: int):
        """
        Adds sentences into latex document
        """

        new_paragraph: str = " ".join([sent for _, sent in transforms_sentences])
        new_paragraph = self._make_colorized_text(text=new_paragraph)
        new_doc: str = doc[:insertion_position] + "\n" + new_paragraph + "\n" + doc[insertion_position:]
        return new_doc

