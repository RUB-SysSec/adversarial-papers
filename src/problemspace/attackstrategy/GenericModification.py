from abc import ABC, abstractmethod
from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.LogSettings import LogSettings
from problemspace.attackstrategy.AttackSettings import AttackSettings


class GenericModification(ABC):
    """
    Generic Modification Class.
    Implemented based on 'decorator' pattern.
    This allows us to chain different *Modification classes together.
    """

    def __init__(self, logsettings: LogSettings, attacksettings: AttackSettings, modifier: 'GenericModification'):
        """
        Init modification class.
        :param logsettings: log settings
        :param attacksettings: attack settings/elements
        :param modifier: generic modifier
        """
        self.logsettings: LogSettings = logsettings
        self.attacksettings: AttackSettings = attacksettings
        self.modifier: modifier = modifier

    @abstractmethod
    def perform_attack(self, transfstate: TransformationState, seed: int) \
            -> TransformationState:
        """
        Performs the transformations on a <TransformationState>
        :param transfstate: latex source state
        :param seed: seed for randomness in experiments
        :return: novel transformation state.
        """
        pass
