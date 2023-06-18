from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.LogSettings import LogSettings
from problemspace.attackstrategy.AttackSettings import AttackSettings
from problemspace.attackstrategy.GenericModification import GenericModification
from problemspace.attackstrategy.RequestedChanges import RequestedChanges


class ProblemSpaceAttackStrategy:
    """
    Generic Problem Space Attack Strategy Interface.

    This class is responsible to find suitable changes in the problem space
    (that is, to the latex / PDF file), such that we obtain the requested
    changes from the feature space.
    """

    def __init__(self, logsettings: LogSettings, attacksettings: AttackSettings):
        """
        Init a problem space strategy.
        :param logsettings: log settings
        :param attacksettings: attack settings/elements
        """
        self.logsettings: LogSettings = logsettings
        self.attacksettings: AttackSettings = attacksettings

    def do_problem_space_attack(self, transfstate: TransformationState,
                                modifier: GenericModification,
                                requested_changes_input: RequestedChanges,
                                seed: int) -> TransformationState:

        if self.attacksettings.problem_space_finish_all is False:
            # A) We do not iterate over multiple targets, so take the best target dict from feature space
            cur_transfstate: TransformationState = transfstate.copyto()
            cur_transfstate.update_target_wordsdict(wordsdict=requested_changes_input.requested_changes_best)
            transfstate = modifier.perform_attack(transfstate=cur_transfstate,
                                                  seed=seed)
            return transfstate

        else:
            # B) Multiple targets from feature space that we can test. Not implemented here. Ignore this option for now.
            raise NotImplementedError("It seems you have set 'problem_space_finish_all=True' as parameter. "
                                      "This parameter was intended to allow the problem-space strategy to test "
                                      "multiple target dictionaries from the feature space instead of only one. "
                                      "As the results for this are not part of the final paper, we removed it here "
                                      "from the repository, as it requires more code changes here and in other parts.")

