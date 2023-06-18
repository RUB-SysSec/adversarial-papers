from typing import List, Dict, Tuple
from problemspace.attackstrategy.Budgeting.ProblemSpaceCostBudgetManager import ProblemSpaceCostBudgetManager, CostBudget


class ProblemSpaceEqualBudgetManager(ProblemSpaceCostBudgetManager):
    """
    Responsible to manage the budget for the problem-space transformations.
    Here we try to distribute the possible changes equally over all feature-problem space switches.
    """

    def __init__(self,
                 budget_transformers: Dict[str, int],
                 cost_transformers: Dict[str, float],
                 feature_problem_switch: int):

        super().__init__(budget_transformers=budget_transformers,
                         cost_transformers=cost_transformers,
                         feature_problem_switch=feature_problem_switch)

    # @Overwrite
    def _calc_modifications(self, budget: int, cost: float) -> List[CostBudget]:
        feature_problem_switch = self.feature_problem_switch
        max_transformations = budget

        transf_per_iteration: List[CostBudget] = [CostBudget() for _ in range(feature_problem_switch)]

        if max_transformations <= feature_problem_switch:
            # we have fewer transformations than feature-problem-switches, so we make 1 transformation per switch
            for i in range(len(transf_per_iteration)):
                transf_per_iteration[i].possible_modifications_per_transformer = 1
                transf_per_iteration[i].cost_per_modification_per_transformer = cost
        else:
            for i in range(len(transf_per_iteration)):
                transf_per_iteration[i].possible_modifications_per_transformer = max_transformations // feature_problem_switch
                transf_per_iteration[i].cost_per_modification_per_transformer = cost

            remaining_ = max_transformations % feature_problem_switch
            if remaining_ > 0:
                # we need to distribute the remaining possible transformations
                for i in range(remaining_):
                    transf_per_iteration[i].possible_modifications_per_transformer += 1

        return transf_per_iteration
