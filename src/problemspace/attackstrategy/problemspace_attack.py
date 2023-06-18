import logging
import pathlib
import json
import typing

from autobid import AutoBid
from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.TransformationState import TransformationState
from problemspace.attackstrategy.ProblemSpaceAttackStrategy import ProblemSpaceAttackStrategy
from problemspace.attackstrategy.GenericModification import GenericModification
from problemspace.attackstrategy.FormatModification import FormatModification
from problemspace.attackstrategy.TextModification import TextModification
from problemspace.attackstrategy.EncodingModification import EncodingModification
from problemspace.attackstrategy.RequestedChanges import RequestedChanges
from problemspace.attackstrategy.AttackSettings import AttackSettings
from problemspace.attackstrategy.Budgeting.ProblemSpaceCostBudgetManager import CostBudget
from problemspace.exceptions.ProblemSpaceException import ProblemSpaceException


def problemspace_attack(logger: logging.Logger,
                        transfstate: TransformationState,
                        requested_changes: RequestedChanges,
                        config: typing.Dict,
                        autobid_models: typing.List[AutoBid],
                        target: dict,
                        clean_pdf_path: pathlib.Path,
                        budget_for_iteration: typing.Dict[str, CostBudget],
                        working_dir: typing.Optional[pathlib.Path] = None,
                        seed: int = 19) -> TransformationState:
    """
    Responsible to start the problem space attack.
    :param logger: logger
    :param transfstate: current transformation state
    :param requested_changes: requested changes from feature space for problem space
    :param config: config dict with more settings for evaluation
    :param autobid_models: AutoBid system
    :param target: the target reviewers
    :param clean_pdf_path: path to clean PDF
    :param budget_for_iteration: cost budget for current iteration
    :param working_dir: pathlib directory where we might be interested in saving information. Can be None if nothing should be saved.
    :param seed: seed for random
    :return: pdf-latex object
    """

    # 1. Save the settings for the attack
    logsettings: LogSettings = LogSettings(
        debug_coloring=config['debug_coloring'],
        logger=logger,
        error_dir=working_dir / "problem-space-errors" if working_dir is not None else None
    )

    attacksettings: AttackSettings = AttackSettings(
        target=target,
        autobid_models=autobid_models,
        clean_pdf_path=clean_pdf_path,
        problem_space_finish_all=config['problem_space_finish_all'],
        budget_transformers=budget_for_iteration,
        synonym_model_path=pathlib.Path(config['synonym_model']),
        stemming_mapping_path=pathlib.Path(config['stemming_map']),
        lang_model_path=pathlib.Path(config['lang_model_path']),
        lang_model_key=config['lang_model_key']
    )

    # 2. Preprocess, TODO currently just quick fix to handle e.g. non-utf8 chars
    requested_changes.clean()
    logger.info("        -> Problem Space Restrictions: Cleaned best features")
    logger.info(str(requested_changes.removed_requested_changes_best))

    # 3. Choose the modification strategy / scenario
    if config['text_level'] is False and config['encoding_level'] is False and config['format_level'] is False:
        raise ProblemSpaceException("No modification strategy chosen")
    modifiers: typing.List[GenericModification] = []

    # if all levels are set, this creates a sequence of text -> encoding -> format
    if config['format_level'] is True:
        modifiers.append(FormatModification(
            logsettings=logsettings,
            attacksettings=attacksettings,
            modifier=None if len(modifiers) == 0 else modifiers[-1]
        ))
    if config['encoding_level'] is True:
        modifiers.append(EncodingModification(
            logsettings=logsettings,
            attacksettings=attacksettings,
            modifier=None if len(modifiers) == 0 else modifiers[-1]
        ))
    if config['text_level'] is True:
        modifiers.append(TextModification(
            logsettings=logsettings,
            attacksettings=attacksettings,
            bibtexfiles=pathlib.Path(config['bibtexfiles']),
            modifier=None if len(modifiers) == 0 else modifiers[-1]
        ))

    # 4. Perform modifications by following a specific strategy in problem space
    problemspace_attackstrategy: ProblemSpaceAttackStrategy = ProblemSpaceAttackStrategy(
        logsettings=logsettings,
        attacksettings=attacksettings,
    )
    adv_transfstate: TransformationState = problemspace_attackstrategy. \
        do_problem_space_attack(transfstate=transfstate,
                                modifier=modifiers[-1],
                                requested_changes_input=requested_changes,
                                seed=seed)

    # Update the blocked features that were cleaned at the very beginning
    adv_transfstate.probspacerestrictions.update(requested_changes.removed_requested_changes_best)

    # 5. Save some results
    if working_dir is not None:
        with open(working_dir / "applied_transformers.json", 'w') as f:
            json.dump(adv_transfstate.applied_transformers, f)
        with open(working_dir / "transformer_history.json", 'w') as f:
            json.dump(adv_transfstate.history, f)
        with open(working_dir / "transformer_history_side_effects.json", 'w') as f:
            json.dump(adv_transfstate.history_side_effects, f)

    return adv_transfstate
