import pathlib
import time
from typing import Optional

from problemspace.transformers.LogSettings import LogSettings
from problemspace.attackstrategy.GenericModification import GenericModification
from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.Transformer import Transformer

from problemspace.transformers.bibtex.BibTexDatabase import BibTexDatabase
from problemspace.transformers.bibtex.BibTexTransformer import BibTexTransformer
from problemspace.transformers.bibtex.BibTexAssignmentSolverParent import BibTexAssignmentSolverParent
from problemspace.transformers.bibtex.BibTexAssignmentSolver2 import BibTexAssignmentSolver2
from problemspace.transformers.SynonymTransformer import SynonymTransformer
from problemspace.transformers.spellingmistakes.SpellingMistakeTransformer import SpellingMistakeTransformer, \
    SpellingMistakeTransformerOption
from problemspace.transformers.bibtex.FakeBibTexTransformer import FakeBibTexTransformer
# from problemspace.transformers.SentenceTransformer.GPT2Transformer import GPT2Transformer
from problemspace.transformers.SentenceTransformer.OurFinedTunedLangModelTransformer import OurFinedTunedLangModelTransformer
from problemspace.attackstrategy.AttackSettings import AttackSettings
from problemspace.transformers.IgnoredEnvironments import IGNORED_ENVS


class TextModification(GenericModification):
    """
    This class implements modifications that work directly on the text.
    """

    def __init__(self,
                 logsettings: LogSettings,
                 attacksettings: AttackSettings,
                 modifier: Optional[GenericModification],
                 bibtexfiles: pathlib.Path,
                 ):

        # A. Parent Class
        super().__init__(logsettings=logsettings, attacksettings=attacksettings, modifier=modifier)

        # B. Load Bibtex Database (or create it if not already created, this should actually only be necessary once)
        self.bibtexfiles = bibtexfiles
        self.bibtexdatabase = BibTexDatabase(verbose=True)
        try:
            self.bibtexdatabase.load_bibtexdatabase_from_pickle(targetfilepath=self.bibtexfiles / "bibsources.pck")
        except FileNotFoundError:
            self.logsettings.logger.info("       -> Creating a new bib tex database")
            self.bibtexdatabase.add_bibfiles_from_disk(self.bibtexfiles)
            self.bibtexdatabase.save_bibtexdatabase_to_pickle(targetfilepath=self.bibtexfiles / "bibsources.pck")

    def perform_attack(self, transfstate: TransformationState, seed: int) \
                -> TransformationState:

        # A. Apply transformations
        start_transformation: float = time.time()
        self.logsettings.logger.info("[   0] Bibtex Transformer started")

        # A.1) Bibtex Transformer
        budget_bibtextransf = self.attacksettings.budget_transformers['BibTexTransformer'].possible_modifications_per_transformer
        bibtexassignmentsolver: BibTexAssignmentSolverParent = BibTexAssignmentSolver2(
            verbose=False, maxpapers=budget_bibtextransf)
        bibtextransf: Transformer = BibTexTransformer(bibtexdatabase=self.bibtexdatabase,
                                                      bibtexassignmentsolver=bibtexassignmentsolver,
                                                      logsettings=self.logsettings)
        transfstate = bibtextransf.apply_transformer(transformationstate=transfstate)

        running_time: int = round(time.time() - start_transformation)
        self.logsettings.logger.info(f"[   0] Bibtex Transformer finished (running time: {(running_time % 60)}s)")

        # A.2) Fake-bibtex Transformer
        start_transformation = time.time()
        self.logsettings.logger.info("[   1] Fake-Bibtex Transformer started")

        budget_faketransf = self.attacksettings.budget_transformers['FakeBibTexTransformer'].possible_modifications_per_transformer
        fakebibtextransf: Transformer = FakeBibTexTransformer(bibtexdatabase=self.bibtexdatabase,
                                                              logsettings=self.logsettings,
                                                              maxpapers=budget_faketransf,
                                                              seed=seed)
        transfstate = fakebibtextransf.apply_transformer(transformationstate=transfstate)

        running_time: int = round(time.time() - start_transformation)
        self.logsettings.logger.info(f"[   1] Fake-Bibtex Transformer finished (running time: {(running_time % 60)}s)")

        # A.3) Synonym Transformer
        start_transformation = time.time()
        self.logsettings.logger.info("[   2] Synonym Transformer started")

        budget_synonymtransf = self.attacksettings.budget_transformers[
            'SynonymTransformer'].possible_modifications_per_transformer
        synonymtransf: SynonymTransformer = SynonymTransformer(logsettings=self.logsettings,
                                                               synonym_model_path=self.attacksettings.synonym_model_path,
                                                               synonym_threshold=0.62,
                                                               pos_checker=1,
                                                               max_changes=budget_synonymtransf,
                                                               ignored_environments=IGNORED_ENVS)
        transfstate = synonymtransf.apply_transformer(transformationstate=transfstate)

        running_time: int = round(time.time() - start_transformation)
        self.logsettings.logger.info(f"[   2] Synonym Transformer finished (running time: {(running_time % 60)}s)")

        # A.4) Spelling Mistake Transformer
        start_transformation = time.time()
        self.logsettings.logger.info("[   3] Spelling-Mistake Transformer started")

        budget_spellmistaketransf = self.attacksettings.budget_transformers['SpellingMistakeTransformer'].possible_modifications_per_transformer
        spellmistaketransf: Transformer = SpellingMistakeTransformer(
            logsettings=self.logsettings,
            ignored_environments=IGNORED_ENVS,
            transformeroption=SpellingMistakeTransformerOption.COMMON_TYPOS_OTHERWISE_TRY_RANDOMLY_SWAP_DELETE,
            max_changes=budget_spellmistaketransf,
            seed=seed)
        transfstate = spellmistaketransf.apply_transformer(transformationstate=transfstate)

        running_time: int = round(time.time() - start_transformation)
        self.logsettings.logger.info(f"[   3] Spelling-Mistake Transformer finished (running time: {(running_time % 60)}s)")

        # A.5) Sentence Transformer
        start_transformation = time.time()
        self.logsettings.logger.info("[   3] OurFinedTunedLangModel Transformer started")

        budget_gptneotransf = self.attacksettings.budget_transformers['OurFinedTunedLangModelTransformer'].possible_modifications_per_transformer
        gptneotransf: Transformer = OurFinedTunedLangModelTransformer(
            logsettings=self.logsettings,
            gptneo_key=self.attacksettings.lang_model_key,
            gptneomodel_path=self.attacksettings.lang_model_path,
            stemming_mapping_path=self.attacksettings.stemming_mapping_path,
            ignored_environments=IGNORED_ENVS,
            max_words=budget_gptneotransf,
            seed=seed)
        transfstate = gptneotransf.apply_transformer(transformationstate=transfstate)

        running_time: int = round(time.time() - start_transformation)
        self.logsettings.logger.info(f"[   3] OurFinedTunedLangModel Transformer finished (running time: {(running_time % 60)}s)")

        # B. final source w/ all changes
        adv_pdflatexsource = transfstate.pdflatexsource
        # compile and return pdf
        adv_pdflatexsource.runpdflatex()

        if self.modifier is not None:
            return self.modifier.perform_attack(transfstate=transfstate, seed=seed)
        else:
            return transfstate