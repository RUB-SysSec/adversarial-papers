from dataclasses import dataclass
import typing



@dataclass()
class BibTexElement:
    """
    Class for keeping track of a bib element
    """
    fields: typing.Dict[str, str]
    uniqueid: str
    # entrytype: str

    def __hash__(self):
        return hash(self.uniqueid)
