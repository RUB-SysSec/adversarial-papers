import typing
import re
import copy
from fuzzywuzzy import fuzz

from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.bibtex.BibTexDatabase import BibTexDatabase
from problemspace.transformers.bibtex.BibTexElement import BibTexElement
from problemspace.transformers.bibtex.BibTexElementKeyworded import BibTexElementKeyworded
from problemspace.transformers.bibtex.Bibtexmatch import Bibtexmatch
from problemspace.transformers.bibtex.BibTexAssignmentSolverParent import BibTexAssignmentSolverParent
from problemspace.transformers.bibtex.BibTexParentTransformer import BibTexParentTransformer
from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.FeatureDelta import FeatureDelta
from utils.pdf_utils import analyze_words_from_string


class BibTexTransformer(BibTexParentTransformer):
    """
    # 1. find out if bib files are in main document or in external bbl file
    # this determines where I have to add new entry

    # 2. as arxiv works on bbl, and latex dir is not guaranteed to have bib files, we work on bbl
    # But we need to mimic the style of bbl files...
    """

    def __init__(self,
                 bibtexdatabase: BibTexDatabase,
                 bibtexassignmentsolver: BibTexAssignmentSolverParent,
                 logsettings: LogSettings):
        """
        :param bibtexdatabase: bibtexdatabase, which contains a list of databases
        :param bibtexassignmentsolver: solver for bibtex transformation
        :param logsettings, # TODO implement debug-coloring
        """
        super().__init__(bibtexdatabase=bibtexdatabase, logsettings=logsettings)

        # threshold for fuzzy string matching to detect if a found bibtex element is already present in paper:
        self.threshold_fuzzy_matching: int = 95
        # solver
        self.bibtexassignmentsolver: BibTexAssignmentSolverParent = bibtexassignmentsolver

    # @Overwritten
    def _transform(self, transformationstate: TransformationState) -> FeatureDelta:
        maindoc: str = transformationstate.pdflatexsource.get_main_document()

        # 1. Find suitable bib tex elements from library
        bibelemsmatched: typing.List[Bibtexmatch] = []
        for keyword, value in transformationstate.current_wordsdict.items():
            if len(keyword) > 3 and value > 0:  # we can only add bibtex elements (value>0) + restriction on keyword.
                bibstoadd: typing.List[BibTexElement] = self.bibtexdatabase.search_string(
                    keyword=keyword,
                    fields=BibTexDatabase.get_stemmed_fields_of_minimal_bibtex_entry())
                if len(bibstoadd) > 0:
                    bibelemsmatched.append(Bibtexmatch(matches=bibstoadd, keyword=keyword, needed_insertions=value))

        # 2. Manipulate file, to this end we find out if we need to change main file or the corresponding bbl file
        isbibsectioninpaper, bibstartindex = self.is_bib_in_paper(maindoc=maindoc)

        # 2.1 Exclude elements that are already present
        if isbibsectioninpaper is True:
            bibtext = BibTexTransformer.load_bib_from_paper(maindoc=maindoc, bibstartindex=bibstartindex)
        else:
            bibtext = BibTexTransformer.load_bib_from_bbl(newpdflatexsource=transformationstate.pdflatexsource)

        self.resolve_present_papers(bibtexelemsmatched=bibelemsmatched, curbib=bibtext)

        # 2.2 Find minimal number of papers to add the wanted words
        bibtexassignment_return: typing.Tuple[typing.List[BibTexElementKeyworded], FeatureDelta] = \
            self.bibtexassignmentsolver.solve(bibelemsmatched=bibelemsmatched)
        bibtexelemstoadd: typing.List[BibTexElementKeyworded] = bibtexassignment_return[0]
        bibtexelemsdelta: FeatureDelta = bibtexassignment_return[1]

        # 2.3 If no suitable entries were found, we stop here!
        if len(bibtexelemstoadd) == 0:
            self.logger.debug(f"        > BibTexTransformer: Abort. Didn't find bibtex entry for keyword list. "
                              f"Len(bibelemsmatched)={len(bibelemsmatched)}, items:"
                              f" {str(transformationstate.current_wordsdict.items())}")
            return FeatureDelta()

        # 2.4 Check if keywords were present in first name of author fields, then add {} around author-name
        bibtexelemstoadd_fn = BibTexTransformer.resolve_first_name_problem(bibtexelemstoadd=bibtexelemstoadd)

        # 2.5 Now manipulate file
        self.change_bibliography(maindoc=maindoc, isbibsectioninpaper=isbibsectioninpaper, bibstartindex=bibstartindex,
                                 transformationstate=transformationstate, bibtexelemstoadd=bibtexelemstoadd_fn)

        return bibtexelemsdelta

    def resolve_present_papers(self, bibtexelemsmatched: typing.List[Bibtexmatch],
                               curbib: str):
        """
        Iterate over all found bibtex elements and check if the title is already present in bib section.
        Removes in bibtexelemsmatched all matched elements.
        :param bibtexelemsmatched: bibtex collections that were matched for a given keyword
        :param curbib: current bib elements in paper
        """

        for bibmatches in bibtexelemsmatched:
            possible_bibtexelemstoadd: typing.List[BibTexElement] = []
            for curbibtexelemtoadd in bibmatches.matches:
                curtitle = curbibtexelemtoadd.fields['title']
                is_present: bool = self.check_paper_present(curtitle=curtitle,
                                                            curbib=curbib,
                                                            threshold_fuzzy_matching=self.threshold_fuzzy_matching)
                if not is_present:
                    possible_bibtexelemstoadd.append(curbibtexelemtoadd)

            bibmatches.matches = possible_bibtexelemstoadd

    @staticmethod
    def split_author_field(author_entry: str, stemmed: bool) -> typing.List:
        """
        Splits the author field into different authors, and first+last name
        :param author_entry: string of bibtex_entry['author']
        :param stemmed: should be the output stemmed?
        :return: different authors, splitted into first + last name
        """

        splitted_author_entries = re.split(" (and|AND) ", author_entry)
        assert len(splitted_author_entries) >= 1

        splitted_author_entries = [x.strip() for x in splitted_author_entries if x.strip().lower() != 'and']

        final_author_output = []
        for authorentry in splitted_author_entries:
            if "," in authorentry:
                authorparts = authorentry.split(",")
            else:
                authorparts = authorentry.split()
            authorparts = [x.strip() for x in authorparts]

            if stemmed:
                authorpartsout = []
                for x in authorparts:
                    out = analyze_words_from_string(x.lower())
                    if len(out) == 1:
                        authorpartsout.append(out[0])
                    elif len(out) > 1:
                        authorpartsout.extend(out)
                authorparts = authorpartsout

            if len(authorparts) == 1:
                # we just have one author name, can happen if we only saved last name without first name
                if "," in authorentry:
                    authorparts = authorparts + ['']
                else:
                    authorparts = [''] + authorparts

            if "," in authorentry:
                final_author_output.append((authorparts[1:], authorparts[0]))
            else:
                final_author_output.append((authorparts[:-1], authorparts[-1]))

        return final_author_output


    @staticmethod
    def resolve_first_name_problem(bibtexelemstoadd: typing.List[BibTexElementKeyworded]) \
            -> typing.List[BibTexElementKeyworded]:
        """
        Resolve problems around the first name in the author field.
        If keyword-to-be-added is in first name(s), then we need to add {} around the name, leading to
        {First Name(s)}. This ensures that first name is printed even if bibtex style says that first name should be
        abbreviated.
        :param bibtexelemstoadd:
        :return: bibtexelemstoadd where first author is sourrounded by {} if keyword is first name
        """

        bibtexelemstoadd_return: typing.List[BibTexElementKeyworded] = []

        for bibentry in bibtexelemstoadd:
            names_stemmed = BibTexTransformer.split_author_field(author_entry=bibentry.fields['author'].lower(),
                                                              stemmed=True)
            names_ = BibTexTransformer.split_author_field(author_entry=bibentry.fields['author'],
                                                              stemmed=False)

            newbibentry = copy.deepcopy(bibentry)
            bibtexelemstoadd_return.append(newbibentry)

            # save in following set all names that need to be enclosed
            namestobeenclosed: typing.Set[int] = set()

            # check if keyword was actually present in first name (only then, we must do sth), or last name,
            # or in another field
            for keyword in bibentry.keywords:
                keyword_l = keyword.lower()

                for i, name in enumerate(names_stemmed):
                    if keyword_l in " ".join(name[0]):
                        namestobeenclosed.add(i)

            if len(namestobeenclosed) == 0:
                continue

            # if keyword in first name(s), then we need to add {First Name(s)} to ensure that first name
            #  is printed even if bibtex style says that first name should be abbreviated.
            newauthorstring: typing.List[str] = []
            for i, curname in enumerate(names_):
                if i in namestobeenclosed:
                    newauthorstring.append('{' + " ".join(names_[i][0]) + " " + names_[i][1] + '}')
                else:
                    newauthorstring.append(" ".join(names_[i][0]) + " " + names_[i][1])

            newbibentry.fields['author'] = " AND ".join(newauthorstring)

        return bibtexelemstoadd_return
