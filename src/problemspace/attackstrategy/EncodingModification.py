from typing import Optional

from problemspace.transformers.LogSettings import LogSettings
from problemspace.attackstrategy.GenericModification import GenericModification
from problemspace.transformers.HomoglyphTransformer import HomoglyphTransformer
from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.Transformer import Transformer
from problemspace.attackstrategy.AttackSettings import AttackSettings
from problemspace.transformers.IgnoredEnvironments import IGNORED_ENVS


class EncodingModification(GenericModification):
    """
    This class implements modifications that aim at the encoding.
    """

    def __init__(self,
                 logsettings: LogSettings,
                 attacksettings: AttackSettings,
                 modifier: Optional[GenericModification],
                 ):
        super().__init__(logsettings=logsettings, attacksettings=attacksettings, modifier=modifier)

    def perform_attack(self, transfstate: TransformationState, seed: int) \
            -> TransformationState:

        # A. Homoglyph transformer.
        self.logsettings.logger.info("[   2] Homoglyph Transformer")
        homoglyphtransf: Transformer = HomoglyphTransformer(logsettings=self.logsettings,
                                                            ignored_environments=IGNORED_ENVS)
        transfstate = homoglyphtransf.apply_transformer(transformationstate=transfstate)
        # self.logger.info(f'      {transfstate.pdflatexsource}')

        # B. Final source w/ all changes
        adv_pdflatexsource = transfstate.pdflatexsource
        # compile and return pdf
        adv_pdflatexsource.runpdflatex()

        if self.modifier is not None:
            return self.modifier.perform_attack(transfstate=transfstate, seed=seed)
        else:
            return transfstate

