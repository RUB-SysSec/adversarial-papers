import numpy as np
import pandas as pd
import typing

from problemspace.transformers.bibtex.BibTexAssignmentSolverParent import BibTexAssignmentSolverParent
from problemspace.transformers.FeatureDelta import FeatureDelta


class BibTexAssignmentSolver2(BibTexAssignmentSolverParent):
    """
    Given the constraint of N papers, this solver tries to find N papers, such that
    the number of added keywords is maximized.

    Let's say we have keyword1, keyword2, keyword3 and paper1, paper2, paper3.
            , paper1, paper2, paper3
    keyword1,   1   ,   0,  ,   1
    keyword2,   1,  ,   0,  ,   1
    keyword3,   1   ,   1   ,   0
    If we have N = 1, we should add paper1 to get the maximum of matched keywords.
    If we have N = 2, we should add paper1 and paper3 to match most of the keywords.

    To this end, this class uses a greedy strategy that sorts all possible papers
    according to the number of keywords that they would add. Finally, it chooses
    the N papers with the highest number of keywords. In other words, with the
    table above, we compute the col-sum, sort it along axis=1, and take the
    N left-most columns.

    However, we only consider a paper to be added if the keyword's occurence is not larger than requested
    (by paperadditions).

    Note: We also tested to solve this as optimization problem (the file was called BibTexAssignmentSolver).
    Hence, the file and class here is BibTexAssignmentSolver2. (We removed BibTexAssignmentSolver from the repo,
    as we did not use it eventually).
    """

    def __init__(self, verbose: bool, maxpapers: int):
        super().__init__(verbose=verbose)
        assert type(maxpapers) is int
        self.maxpapers: int = maxpapers

    # @Overwrite
    def get_assignment(self, papertable: pd.DataFrame, paperadditions: pd.DataFrame) \
            -> typing.Tuple[typing.Set[str], FeatureDelta]:

        # Sort papertable in descending order w.r.t column sum.
        sx = papertable.columns[np.argsort(papertable.sum(axis=0))[::-1]]
        papertable_sorted = papertable.loc[:, sx]

        # Get N papers
        paperstobeadded = set()
        keyword_additions = pd.DataFrame(0, index=papertable.index, columns=['additions'])
        for (columnName, columnData) in papertable_sorted.iteritems():

            # check constraint about max papers
            if len(paperstobeadded) >= self.maxpapers:
                break

            # check constraint that no paper is added that adds a keyword more than it should be
            if np.sum(keyword_additions['additions'] + columnData > paperadditions['additions']) == 0:
                keyword_additions['additions'] += columnData
                paperstobeadded.add(columnName)

        # Also save what keywords were now considered and how many papers do we add == how often do we add the keyword
        finalkeyworddict: FeatureDelta = FeatureDelta()
        for crow, cval in keyword_additions.iterrows():
            if cval['additions'] != 0:  # only keywords that are added
                finalkeyworddict.changes[str(crow)] = int(cval['additions'])

        return paperstobeadded, finalkeyworddict
