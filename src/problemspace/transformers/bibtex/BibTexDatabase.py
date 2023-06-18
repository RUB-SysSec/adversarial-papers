import time
import pathlib
import typing
from typing import List
import pickle
import bibtexparser

from utils.pdf_utils import analyze_words_from_string
from problemspace.transformers.bibtex.BibTexElement import BibTexElement


class BibTexDatabase:
    """
    Represents various bibtex files.
    """

    def __init__(self, verbose: bool = False):
        self.bibtex_databases: List[bibtexparser.bibdatabase.BibDatabase] = []
        self.verbose = verbose

    def add_bibfiles_from_disk(self, bibtexfilesdir: pathlib.Path) -> None:
        """
        Loads bib files
        """
        if not bibtexfilesdir.exists():
            raise ValueError("Bibtex dir does not exist")

        bibfiles: list = []
        for bibfile in bibtexfilesdir.glob("*.bib"):
            if self.verbose is True:
                print(f"Bib found: {bibfile}")
            bibfiles.append(bibfile)

        a = time.time()
        for i, bibfile in enumerate(bibfiles):
            if self.verbose is True and i % 5 == 0:
                print(f"Loading bibtex bibs: {i}/{len(bibfiles)} processed...")
            with open(bibfile, "r") as bibtex_file:
                self.bibtex_databases.append(bibtexparser.load(bibtex_file))
        b = time.time()
        if self.verbose is True:
            print(f"Loading took {b - a}s")

        c = time.time()
        self.remove_problem_entries()
        self.postprocessing_stemming()
        self.remove_unvalid_characters()
        d = time.time()
        if self.verbose:
            print(f"Postprocessing took {d - c}s")

    def load_bibtexdatabase_from_pickle(self, targetfilepath: pathlib.Path):
        """
        Loads from pickle file and appends to inner list of bibtex databases.
        """
        if not targetfilepath.exists():
            raise FileNotFoundError(f"Target file does not exists: {targetfilepath}")
        with open(targetfilepath, 'rb') as handle:
            dat = pickle.load(handle)
            self.bibtex_databases.extend(dat)

    def save_bibtexdatabase_to_pickle(self, targetfilepath: pathlib.Path, overwrite: bool = False) -> None:
        """
        Save database to pickle file
        :param targetfilepath target directory + filename
        :param overwrite if true, existing file will be overwritten
        """

        if overwrite is False and targetfilepath.exists():
            raise ValueError("Target file already exists, but overwrite is set to False")
        assert targetfilepath.parent.exists()

        with open(targetfilepath, 'wb') as handle:
            pickle.dump(self.bibtex_databases, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def remove_problem_entries(self) -> None:
        """
        Remove entries that can cause a problem.
        Currently, we just remove bibtex entries that have no even number of '$' (in this case, $ might be used
        as $ itself, or to introduce a math environment, such as '$-Test $x^2$' as title. If the number is even,
        we assume/hope it is used as math notation and leave it as it is.
        """
        for bib_database in self.bibtex_databases:
            bib_database.entries = [x for x in bib_database.entries if x['title'].count("$") % 2 == 0]

    def postprocessing_stemming(self) -> None:
        """
        Runs over database and applies stemming to all bibtex elements and fields, except ID.
        We have to do so, since we are searching for stemmed words later.
        In addition, it saves each stemmed version, as we will need the original elements for insertion later.
        Dict thus has e.g. booktitle and booktitle_stemmed now for any field, except 'ID'.
        """
        for bib_database in self.bibtex_databases:
            for bibentry in bib_database.entries:
                dkeys = list(bibentry.keys()) # list(.) required, as we change size of dict/keys() during iteration
                for k in dkeys:
                    if k != "ID":
                        processed_field: typing.List[str] = analyze_words_from_string(text=bibentry[k].lower())
                        bibentry[k + "_stemmed"] = " ".join(processed_field)

    def remove_unvalid_characters(self, max_ord_value: int = 256) -> None:
        """
        Cleans bibtex entries from unvalid characters (ord(character)>256 per default are simply removed).
        For non-ascii, set max_ord_value = 128.

        This function might modify the bibtex title, for instance, but this will only affect a few characters
        which is plausible since benign authors might also overlook
        that their bibtex cannot compile these characters.
        """
        def remove_unvalid_characters(s, max_ord_removal = 256):
            return "".join(c for c in s if ord(c) < max_ord_removal)
        def max_ord(s):
            return max(ord(c) for c in s)

        for bib_database in self.bibtex_databases:
            for i, bibentry in enumerate(bib_database.entries):
                for k, v in bibentry.items():

                    # 1) Clean title, author, booktitle if necessary
                    if k in ["title", "author", "booktitle", "journal"]: # only non-stemmed fields where we expect non-ascii characters.
                        if max_ord(v) >= max_ord_value:
                            # print(k, v, max_ord(v))
                            bibentry[k] = remove_unvalid_characters(s=v, max_ord_removal=max_ord_value)

                            # we should also re-compute the stemmed version
                            processed_field: typing.List[str] = analyze_words_from_string(text=bibentry[k].lower())
                            bibentry[k + "_stemmed"] = " ".join(processed_field)

                    # 2) Clean key; we get less problems if the keys are ascii
                    if k == "ID":
                        if max_ord(v) >= 128:
                            bibentry[k] = remove_unvalid_characters(s=v, max_ord_removal=128)


    def search_string(self,
                      keyword: str,
                      fields: typing.Optional[typing.List[str]] = None,
                      ) -> typing.List[BibTexElement]:
        """
        Search for keyword in bibtex entries in the stored databases
        :param keyword: keyword to be searched
        :param fields: either none or if specified, a list of bibtex fields where function searches for keyword
        :return: list of matched bibtex entries
        """
        keyword_l = keyword.lower()

        matches = []
        for bib_database in self.bibtex_databases:
            for bibentry in bib_database.entries:
                for k, v in bibentry.items():
                    if fields is not None and k not in fields:
                        continue
                    if keyword_l in v.lower().split():
                        matches.append(BibTexElement(fields=bibentry, uniqueid=bibentry['ID']))
                        break

        return matches

    # @staticmethod
    # def create_minimal_bibtex_entry(bibtex_entry: dict) -> str:
    #     """
    #     Converts bib tex element to string version that can be included in a bib file for bibtex.
    #     :param bibtex_entry: bib element
    #     :return: string version of bib element
    #     """
    #     minimalentry = {}
    #     for k, v in bibtex_entry.items():
    #         if k in ['ENTRYTYPE', 'ID', 'author', 'booktitle', 'journal', 'title', 'pages']:
    #             minimalentry[k] = v
    #     writerb = BibTexWriter()
    #     return writerb._entry_to_bibtex(minimalentry)

    @staticmethod
    def create_minimal_bibtex_entry2(bibtex_entry: dict) -> str:
        """
        Alternative to create_minimal_bibtex_entry that creates string manually without bibtexparser
        """
        # We might need to replace special characters only in specific fields
        title_processed = bibtex_entry['title']
        title_processed = title_processed.replace("_", "\_")

        # Create bibtex entry
        newentry = f"@{bibtex_entry['ENTRYTYPE']}{{{bibtex_entry['ID']},\n" \
                   f"\t author = {{{bibtex_entry['author']}}},\n"

        if 'booktitle' in bibtex_entry:
            newentry += f"\t booktitle = {{{bibtex_entry['booktitle']}}},\n"
        if 'journal' in bibtex_entry:
            newentry += f"\t journal = {{{bibtex_entry['journal']}}},\n"

        if 'year' in bibtex_entry:
            newentry += f"\t year = {{{bibtex_entry['year']}}},\n"

        newentry += f"\t title = {{{title_processed}}}"
        if 'pages' in bibtex_entry:
            newentry += f",\n\t pages = {{{bibtex_entry['pages']}}}\n}}"
        else:
            newentry += "\n}}"

        # We might need to replace special characters at multiple fields
        newentry = newentry.replace("&", "\&")

        return newentry

    @staticmethod
    def get_fields_of_minimal_bibtex_entry() -> typing.List[str]:
        return ['author', 'booktitle', 'journal', 'title', 'pages']

    @staticmethod
    def get_stemmed_fields_of_minimal_bibtex_entry() -> typing.List[str]:
        return [x + "_stemmed" for x in BibTexDatabase.get_fields_of_minimal_bibtex_entry()]

