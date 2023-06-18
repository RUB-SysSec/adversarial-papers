from dataclasses import dataclass
import typing



@dataclass()
class BibTexElementKeyworded:
    """
    Class for keeping track of a bib element + the keywords that were matched due to this bibtex element
    """
    fields: typing.Dict[str, str]
    uniqueid: str
    keywords: typing.Set[str]


    def __hash__(self):
        return hash(self.uniqueid)
