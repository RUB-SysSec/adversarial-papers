from dataclasses import dataclass
import typing

from problemspace.transformers.bibtex.BibTexElement import BibTexElement


@dataclass(unsafe_hash=True)
class Bibtexmatch:
    """
    Class for keeping track of the bibtex elements that can be added for a specific keyword
    """
    matches: typing.List[BibTexElement]
    keyword: str
    needed_insertions: int