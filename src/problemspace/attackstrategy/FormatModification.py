from typing import Optional

from problemspace.transformers.LogSettings import LogSettings
from problemspace.attackstrategy.GenericModification import GenericModification
from problemspace.transformers.CommentBoxAddWordTransformer import CommentBoxAddWordTransformer
from problemspace.transformers.CommentBoxDelWordTransformer import CommentBoxDelWordTransformer
from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.Transformer import Transformer
from problemspace.attackstrategy.AttackSettings import AttackSettings
from problemspace.transformers.IgnoredEnvironments import IGNORED_ENVS


class FormatModification(GenericModification):
    """
    This class implements modifications that work on the format level.
    """

    def __init__(self,
                 logsettings: LogSettings,
                 attacksettings: AttackSettings,
                 modifier: Optional[GenericModification],
                 ):
        super().__init__(logsettings=logsettings, attacksettings=attacksettings, modifier=modifier)

    def perform_attack(self, transfstate: TransformationState, seed: int) \
            -> TransformationState:

        # A.1 Let's add words.
        # Note that CommentBoxAddWordTransformer will try to add the box on words that need to be removed,
        # so that we achieve both: adding and removing. If not possible, it just adds words.
        self.logsettings.logger.info("[   0] Comment-Add Box Transformer")
        commentboxtransf: Transformer = CommentBoxAddWordTransformer(logsettings=self.logsettings,
                                                                     ignored_environments=IGNORED_ENVS)
        transfstate = commentboxtransf.apply_transformer(transformationstate=transfstate)
        # self.logger.info(f'      {transfstate.pdflatexsource}')

        # A.2 Let's remove words only.
        self.logsettings.logger.info("[   1] Comment-Del Box Transformer")
        commentboxdeltransf: Transformer = CommentBoxDelWordTransformer(logsettings=self.logsettings,
                                                                        ignored_environments=IGNORED_ENVS)
        transfstate = commentboxdeltransf.apply_transformer(transformationstate=transfstate)
        # self.logger.info(f'      {transfstate.pdflatexsource}')

        # B. final source w/ all changes
        adv_pdflatexsource = transfstate.pdflatexsource
        # compile and return pdf
        adv_pdflatexsource.runpdflatex()

        if self.modifier is not None:
            return self.modifier.perform_attack(transfstate=transfstate, seed=seed)
        else:
            return transfstate
