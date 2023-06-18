import time
from pathlib import Path
from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.Transformer import Transformer
from problemspace.transformers.SentenceTransformer.OurFinedTunedLangModelTransformer import OurFinedTunedLangModelTransformer
from problemspace.tests.unittesting.UnitBaseClass import UnitBaseClass
from problemspace.transformers.TransformationState import TransformationState
from utils.pdf_utils import analyze_words


class TestOurFinedTunedLangModelTransformer(UnitBaseClass):

    def setUp(self):
        """
        Runs before any test.
        """
        self.setup_all(default_latex_project="unit_latex_2")

        self.gptpath = self.problemspace_path / Path("misc/huggingface/mymodels/secpapermodels/")
        # self.gptkey = "EleutherAI/gpt-neo-125M"
        self.gptkey = "facebook/opt-350m"

    def test_gptneo_opt_1(self):
        wordsdict = {'CPU2020': 3, 'x64': -1, 'LSTM': 3, 'multithread': 1, 'predict': 1,
                     'current': 1, 'light': 2, 'contribut': 1, 'optim': 1, 'talk': 1,
                     'solv': 1, 'focu': 1, 'secur': 2, 'relat': 4, 'perform': 1, 'upcom': 1,
                     'approach': 2, 'solut': 2}
        expected_delta = {'imag': 1, 'object': 1, 'geo': 1, 'contribuiv': -1, 'algorithm': 1, 'gradient': 3,
                          'imagesc': -1, 'evas': 1, 'loss': 1, 'iv': 1, 'differenti': 1, 'scale': 1, 'attempt': 1,
                          'contribuin': 1, 'descent': 2, 'propos': 1, 'method': 1, 'directli': 1, 'detect': 1,
                          'function': 2, 'exampl': 1, 'adversari': 1, 'paper': 1, 'via': 1,
                          'light': 1, 'optim': 2, 'approach': 1}

        start_time: float = time.time()
        transf: Transformer = OurFinedTunedLangModelTransformer(logsettings=LogSettings(debug_coloring=True), max_words=5,
                                                                gptneo_key=self.gptkey, gptneomodel_path=self.gptpath,
                                                                seed=11 + 211)
        self._test_sentence_transformer(wordsdict=wordsdict, transf=transf, expected_delta=expected_delta,
                                        start_time=start_time)

    def _test_sentence_transformer(self, wordsdict, transf, expected_delta, start_time):
        transfstate: TransformationState = TransformationState(pdflatexsource=self.newpdflatexsource,
                                                               original_wordsdict=wordsdict)
        newtransfstate = transf.apply_transformer(transformationstate=transfstate)
        running_time: int = round(time.time() - start_time)
        print(f"Running time: {running_time}s")

        word_vector_after: list = analyze_words(
            pdf_file=newtransfstate.pdflatexsource.get_maindocument_tempfile(suffix="pdf"))

        UnitBaseClass.check_counts_before_and_after_valuebased(word_vector_before=self.word_vector_before,
                                                               word_vector_after=word_vector_after,
                                                               ignore_words=expected_delta)
