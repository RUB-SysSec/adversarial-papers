import collections
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TRANSFORMERS_VERBOSITY'] = 'critical'

from pathlib import Path
from typing import List, Optional, Tuple
import transformers
from transformers import GPT2Tokenizer, OPTForCausalLM
# from transformers import GPTNeoForCausalLM

from utils.attack_utils import clean_text
from utils.pdf_utils import analyze_words_from_string
from problemspace.transformers.FeatureDelta import FeatureDelta
from problemspace.transformers.LogSettings import LogSettings
from problemspace.exceptions.TransformerException import TransformerException
from problemspace.transformers.SentenceTransformer.LangModelTransformer import LangModelTransformer
from problemspace.transformers.SentenceTransformer.langmodels_utils import get_text, clean_general_paper_text, \
    process_created_text


class OurFinedTunedLangModelTransformer(LangModelTransformer):
    """
    Creates sentences with words-to-be-added based on (finetuned) GPT-Neo / Opt.
    """

    def __init__(self,
                 logsettings: LogSettings,
                 gptneomodel_path: Path,
                 gptneo_key: str,
                 seed=11,
                 stemming_mapping_path: Optional[Path] = None,
                 max_words=None,
                 ignored_environments=[]):

        super().__init__(logsettings=logsettings,
                         seed=seed,
                         stemming_mapping_path=stemming_mapping_path,
                         max_words=max_words,
                         ignored_environments=ignored_environments)

        self.gptneomodel_path: Path = gptneomodel_path
        self.gpt2tokenizer = GPT2Tokenizer.from_pretrained(gptneo_key)
        self.model = OPTForCausalLM.from_pretrained(gptneomodel_path / gptneo_key)
        # self.model = GPTNeoForCausalLM.from_pretrained(gptneomodel_path / gptneo_key)

        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        transformers.set_seed(self.seed)

    # @Overwrite
    def _transform_main_part(self,
                             current_wordsdict: dict,
                             doc: str,
                             insertion_position: int) -> Tuple[FeatureDelta, List[Tuple[str, str]]]:

        tokens_before: int = 250
        text_before_insertion: str = doc[(insertion_position-tokens_before):insertion_position]
        text_before_insertion = clean_general_paper_text(text=text_before_insertion)

        feature_delta: FeatureDelta = FeatureDelta()
        new_sentences: List[Tuple[str, str]] = []
        ignore_stemming: bool = False

        # A. Preparation
        prompt = text_before_insertion

        # B. Prepare word input
        words_to_be_added_raw = [k for k, v in current_wordsdict.items() if v > 0]
        words_to_be_added: List[str] = []
        for next_word in words_to_be_added_raw:
            unstemmed_next_word = self._get_word_for_stemmed_word(stemmed_word=next_word)
            if unstemmed_next_word is not None:
                words_to_be_added.append(unstemmed_next_word)
            elif ignore_stemming:
                words_to_be_added.append(next_word)

        if len(words_to_be_added) == 0:
            self.printlogdebug(f"ProblemSpace: LangModel, no words in input: {len(words_to_be_added)}, "
                               f"{len(words_to_be_added_raw)}")
            return feature_delta, new_sentences

        # C. Apply GPT-Neo / Opt / other lang model
        gentexts, scores = get_text(prompt=prompt, force_words=words_to_be_added,
                                    max_groups=self.max_words, group_size=5,
                                    model=self.model, tokenizer=self.gpt2tokenizer)
        if scores[0] == 0:
            raise TransformerException("ProblemSpace: No word could be added in OurFinedTunedLangModelTransformer")
        created_text_wo_prompt = gentexts[0][len(prompt):]
        created_text: str = clean_general_paper_text(text=created_text_wo_prompt)

        # D. Post-process text
        new_text: str = process_created_text(created_text=created_text, nlp=self.nlp)
        new_text = clean_text(input_text=new_text, logger=self.logger, max_ord_value=255)

        # E. Get information about added words, save information
        tokens_in_new_text: List = analyze_words_from_string(new_text)
        words_added_inthissentence = set.intersection(set(tokens_in_new_text), set(words_to_be_added_raw))


        new_sentences.append(("_".join(words_added_inthissentence), new_text))
        tokens_in_new_text_counter = collections.Counter(tokens_in_new_text)
        for wx in words_added_inthissentence:
            occurences = tokens_in_new_text_counter[wx]
            assert occurences > 0
            feature_delta.changes[wx] = feature_delta.changes.get(wx, 0) + occurences

        return feature_delta, new_sentences

    # @Overwrite
    # Overwritten, to avoid \n after new paragraph
    def _apply_transforms_sentences(self, doc: str,
                                    transforms_sentences: List[Tuple[str, str]],
                                    insertion_position: int):
        """
        Adds sentences into latex document
        """

        new_paragraph: str = " ".join([sent for _, sent in transforms_sentences])
        new_paragraph = self._make_colorized_text(text=new_paragraph)

        new_doc: str = doc[:insertion_position] + new_paragraph + "\n" + doc[insertion_position:]
        return new_doc
