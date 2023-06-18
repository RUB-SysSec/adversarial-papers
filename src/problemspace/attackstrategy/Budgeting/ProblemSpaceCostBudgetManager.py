from typing import List, Dict, Tuple
from problemspace.exceptions.ProblemSpaceException import ProblemSpaceException
from abc import abstractmethod


class CostBudget:

    def __init__(self):
        self.possible_modifications_per_transformer: int = -1
        self.cost_per_modification_per_transformer: float = -1.0


class ProblemSpaceCostBudgetManager:
    """
    Responsible to manage the budget for the problem-space transformations.
    We may have a maximum number of modifications per transformer, and
    a respective number of modifications per iteration. We need to keep track of this.
    """

    def __init__(self,
                 budget_transformers: Dict[str, int],
                 cost_transformers: Dict[str, float],
                 feature_problem_switch: int):

        self.feature_problem_switch: int = feature_problem_switch
        self.budget_transformers: Dict[str, int] = budget_transformers
        self.cost_transformers: Dict[str, float] = cost_transformers

        self.costbudget_per_iteration_per_transformer: Dict[str, List[CostBudget]] = {}

        for k, v in self.budget_transformers.items():
            x = self._calc_modifications(budget=v, cost=cost_transformers[k])
            self.costbudget_per_iteration_per_transformer[k] = x

    def get_costbudget_for_iteration(self, iteration: int) -> Dict[str, CostBudget]:
        output = {}
        for k, v in self.costbudget_per_iteration_per_transformer.items():
            if iteration >= len(v):
                raise ProblemSpaceException("More iterations asked than initially specified during budgeting")
            output[k] = v[iteration]
        return output

    @abstractmethod
    def _calc_modifications(self, budget: int, cost: float) -> List[CostBudget]:
        raise NotImplementedError()
