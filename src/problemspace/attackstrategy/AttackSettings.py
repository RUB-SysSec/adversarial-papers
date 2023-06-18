from dataclasses import dataclass
import typing
from pathlib import Path
from problemspace.attackstrategy.Budgeting.ProblemSpaceCostBudgetManager import CostBudget
from autobid import AutoBid


@dataclass()
class AttackSettings:
    """
    Class for saving attack elements
    """
    target: typing.Dict
    autobid_models: typing.List[AutoBid]
    clean_pdf_path: Path
    problem_space_finish_all: bool
    budget_transformers: typing.Dict[str, CostBudget]
    synonym_model_path: Path
    stemming_mapping_path: Path
    lang_model_path: Path
    lang_model_key: str


