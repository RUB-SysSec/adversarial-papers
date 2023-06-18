import pandas as pd
from abc import ABC, abstractmethod
import typing

from problemspace.transformers.bibtex.BibTexElement import BibTexElement
from problemspace.transformers.bibtex.BibTexElementKeyworded import BibTexElementKeyworded
from problemspace.transformers.bibtex.Bibtexmatch import Bibtexmatch
from problemspace.transformers.FeatureDelta import FeatureDelta


class BibTexAssignmentSolverParent(ABC):
    """
    Returns a set of papers that can be included, given the constraints:
    keywords, papers, maximum number of included papers
    """

    def __init__(self, verbose: bool):
        self.verbose = verbose

    @abstractmethod
    def get_assignment(self, papertable: pd.DataFrame, paperadditions: pd.DataFrame) \
            -> typing.Tuple[typing.Set[str], FeatureDelta]:
        """
        Computes the assignment.
        :param papertable: the pandas table with rows=keywords, columns=papers, value=1 if paper contains keyword
        :param paperadditions: pandas table with rows=keywords, columns= necessary/wanted additions
        :return: tuple of set of string with papers (their unique id),
        the achieved additions per keyword as feature delta object
        """
        pass

    def solve(self, bibelemsmatched: typing.List[Bibtexmatch]) \
            -> typing.Tuple[typing.List[BibTexElementKeyworded], FeatureDelta]:
        """
        Computes papers that should be included
        :param bibelemsmatched: matched, possible bib elements
        :return: list of possible bibtex elements, and delta (keyword - additions - dict).
        """

        # A. Build keyword and paper list
        papersdict = set()
        keywords = []
        for bibmatches in bibelemsmatched:
            for bibmatch in bibmatches.matches:
                if bibmatch.uniqueid not in papersdict:
                    papersdict.add(bibmatch.uniqueid)
                # elif self.verbose is True:
                #     print("redundant element:", bibmatch.uniqueid)
            keywords.append(bibmatches.keyword)

        paperslist = list(papersdict)
        paperslist.sort()
        keywords.sort()

        # B. Build keyword - bib element assignment table
        papertable = pd.DataFrame(0, index=keywords, columns=paperslist)
        paperadditions = pd.DataFrame(0, index=keywords, columns=['additions'])

        for bibmatches in bibelemsmatched:
            for bibmatch in bibmatches.matches:
                bibkey = bibmatch.uniqueid
                papertable.loc[bibmatches.keyword, bibkey] = 1
            # If we have not found enough entries for keyword, we have to decrease the needed insertions:
            paperadditions.loc[bibmatches.keyword, 'additions'] = min(bibmatches.needed_insertions,
                                                                      len(bibmatches.matches))

        # C. Get assignment
        paperstobeadded, finalkeyworddict = self.get_assignment(papertable=papertable,
                                                                paperadditions=paperadditions)

        # D. Prepare output list, we want the BibTexElement objects + keywords (--> BibTexElementKeyworded)
        # Avoid that a paper is added multiple times by using a dict
        finalpapers: typing.Dict[str, BibTexElementKeyworded] = {}
        for bibmatches in bibelemsmatched:
            for bibmatch in bibmatches.matches:
                bibkey = bibmatch.uniqueid

                if bibkey in paperstobeadded:
                    # If paper is present multiple times due to different keywords, we just add the keyword.
                    # No need to save the bibtex element multiple times.
                    if bibmatch.uniqueid not in finalpapers:
                        finalpapers[bibmatch.uniqueid] = BibTexElementKeyworded(fields=bibmatch.fields,
                                                                                   keywords=set(),
                                                                                   uniqueid=bibmatch.uniqueid)
                    finalpapers[bibmatch.uniqueid].keywords.add(bibmatches.keyword)


        finalpapersreturn: typing.List[BibTexElementKeyworded] = list(finalpapers.values())
        finalpapersreturn.sort(key=lambda x: x.uniqueid, reverse=False)

        return finalpapersreturn, finalkeyworddict
