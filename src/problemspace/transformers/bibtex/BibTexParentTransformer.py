import typing
import re
import pathlib
from abc import abstractmethod
from fuzzywuzzy import fuzz

from problemspace.transformers.LogSettings import LogSettings
from problemspace.exceptions.TransformerException import TransformerException
from problemspace.exceptions.PdfLatexException import PdfLatexException
from problemspace.transformers.Transformer import Transformer
from problemspace.transformers.bibtex.BibTexDatabase import BibTexDatabase
from problemspace.transformers.bibtex.BibTexElementKeyworded import BibTexElementKeyworded
from problemspace.transformers.TransformationState import TransformationState
from problemspace.PdfLatexSource import PdfLatexSource
from problemspace.transformers.FeatureDelta import FeatureDelta


class BibTexParentTransformer(Transformer):
    """
    Parent class for bibtex transformations...
    """

    def __init__(self,
                 bibtexdatabase: BibTexDatabase,
                 logsettings: LogSettings):
        """
        :param bibtexdatabase: bibtexdatabase, which contains a list of databases
        :param logsettings, # TODO implement debug-coloring
        """
        super().__init__(logsettings=logsettings)

        # bibtex database that contains possible bibtex elements
        self.bibtexdatabase: BibTexDatabase = bibtexdatabase

    @abstractmethod
    def _transform(self, transformationstate: TransformationState) -> FeatureDelta:
        pass

    @staticmethod
    def is_bib_in_paper(maindoc: str) -> typing.Tuple[bool, int]:
        """
        Finds out if bibliography is defined in main document, returns startposition there if so.
        :param maindoc: main document
        :return: tuple (bool to indicate if bibliography is within maindoc, starting position in maindoc if so)
        """
        bibstartindex: int = maindoc.find("\\begin{thebibliography}")
        isbibsectioninpaper: bool = True if bibstartindex != -1 else False

        return isbibsectioninpaper, bibstartindex

    def check_paper_present(self, curtitle: str, curbib: str, threshold_fuzzy_matching: int) -> bool:
        """
        Check if paper title is already present in bib
        :param curtitle: current title
        :param curbib: current bibliography
        :param threshold_fuzzy_matching: threshold for similarity matching
        :return: true if found in bibliography, else false
        """
        # TODO this leads to some false positives, but we can live with that right now, but could be improved.
        token_sort_ratio = fuzz.token_set_ratio(curtitle, curbib)
        if token_sort_ratio <= threshold_fuzzy_matching:
            return False
        else:
            # self.printlogdebug(msg=f"        > BibTex: I've detected redundant element: {curtitle}")
            return True

    @staticmethod
    def load_bib_from_bbl(newpdflatexsource: PdfLatexSource) -> str:
        """
        Load bib elements from paper's bbl file.
        """

        bblfilepath: pathlib.Path = newpdflatexsource.get_maindocument_tempfile(suffix="bbl")
        if not bblfilepath.exists():
            raise TransformerException(
                "No bbl file found, but this file must exist since no bib is given in main file. Maybe I am missing something. Check this case")
        bblfile: str = bblfilepath.read_text()
        return bblfile

    @staticmethod
    def load_bib_from_paper(maindoc: str,
                            bibstartindex: int) -> str:
        """
        Load bib elements from paper text.
        """
        bibendindex = maindoc.find("\\end{thebibliography}")
        assert bibendindex != -1

        return maindoc[bibstartindex:bibendindex]

    def change_bibliography(self,
                            maindoc: str,
                            isbibsectioninpaper: bool,
                            bibstartindex: int,
                            transformationstate: TransformationState,
                            bibtexelemstoadd: typing.List[BibTexElementKeyworded]):

        if isbibsectioninpaper is True:
            self.change_bibliography_in_paper(newpdflatexsource=transformationstate.pdflatexsource,
                                              maindoc=maindoc,
                                              bibstartindex=bibstartindex,
                                              bibtexelemstoadd=bibtexelemstoadd)
        else:
            self.change_bibliography_in_bbl_file(
                newpdflatexsource=transformationstate.pdflatexsource, maindoc=maindoc,
                bibstartindex=bibstartindex, bibtexelemstoadd=bibtexelemstoadd)

    def create_bbl_elements(self,
                            maindocwithoutbib: str,
                            pdflatexsource: PdfLatexSource,
                            bibtexstoadd: typing.List[str]) -> str:

        biblatexsource: PdfLatexSource = pdflatexsource.copyto()

        biblatexsource.get_filepath_in_dir(filename="attack.bib").write_text("\n".join(bibtexstoadd))

        try:
            biblatexsource.save_latex(newmaindoc=maindocwithoutbib)
            biblatexsource.runpdflatex()
            biblatexsource.runbibtex()
            biblatexsource.runpdflatex()
        except PdfLatexException:
            self.saveerrorlatexsource(pdflatexsource=biblatexsource)
            raise

        bblfilepath: pathlib.Path = biblatexsource.get_maindocument_tempfile(suffix="bbl")
        bblfile: str = bblfilepath.read_text()
        bibitemindices: typing.List[int] = [m.start() for m in re.finditer(r'\\bibitem', bblfile)]
        assert len(bibitemindices) >= 1

        endindexofbibitems: int = bblfile.find("\\end{thebibliography}")
        assert endindexofbibitems != -1

        parsed_bblbibitems: str = bblfile[bibitemindices[0]: endindexofbibitems]

        del biblatexsource

        return parsed_bblbibitems

    def change_bibliography_in_paper(self,
                                     newpdflatexsource: PdfLatexSource,
                                     maindoc: str,
                                     bibstartindex: int,
                                     bibtexelemstoadd: typing.List[BibTexElementKeyworded]):

        # create a string version for all bibtex elements
        curbibtexstoadd = [BibTexDatabase.create_minimal_bibtex_entry2(x.fields) for x in bibtexelemstoadd]

        bibendindex = maindoc.find("\\end{thebibliography}")
        assert bibendindex != -1
        bibendindex += len("\\end{thebibliography}")

        # cut out bib section, add custom bib file, compile it, get bbl elements and add them to bib section
        citecmds = "".join([f"\cite{{{curbibtexelemtoadd.uniqueid}}}" for curbibtexelemtoadd in bibtexelemstoadd])
        mdwithoutbib = maindoc[:bibstartindex] + f"{citecmds}\n" + "\\bibliography{attack}\n" + maindoc[bibendindex:]

        parsed_bblbibitems = self.create_bbl_elements(maindocwithoutbib=mdwithoutbib,
                                                      pdflatexsource=newpdflatexsource,
                                                      bibtexstoadd=curbibtexstoadd)

        bibendindex = maindoc.find("\\end{thebibliography}")
        assert bibendindex != -1

        mdwith_parsed_bblbibitems = maindoc[:bibendindex] + parsed_bblbibitems + maindoc[bibendindex:]
        newpdflatexsource.save_latex(mdwith_parsed_bblbibitems)


    def change_bibliography_in_bbl_file(self,
                                        newpdflatexsource: PdfLatexSource,
                                        maindoc: str,
                                        bibstartindex: int,
                                        bibtexelemstoadd: typing.List[BibTexElementKeyworded]):

        curbibtexstoadd = [BibTexDatabase.create_minimal_bibtex_entry2(x.fields) for x in bibtexelemstoadd]

        bibincludestartindex = maindoc.find("\\bibliography{")
        if bibincludestartindex == -1:
            raise TransformerException(
                "No begin-bibliography and no bibliography include found. Maybe I am missing something. Check this case")

        # find end of \bibliography{bibfile}
        bibincludeendindex = maindoc[bibincludestartindex:].find("}")
        assert bibincludeendindex != -1

        citecmds = "".join([f"\cite{{{curbibtexelemtoadd.uniqueid}}}" for curbibtexelemtoadd in bibtexelemstoadd])
        mdwithoutbib = maindoc[:bibincludestartindex] + f"{citecmds}\n" + "\\bibliography{attack}\n" \
                       + maindoc[(bibincludestartindex + bibincludeendindex + 1):]

        # now move to biblatexsource to get element...
        parsed_bblbibitems = self.create_bbl_elements(maindocwithoutbib=mdwithoutbib,
                                                      pdflatexsource=newpdflatexsource,
                                                      bibtexstoadd=curbibtexstoadd)

        # now append new bbl items to original bbl file
        bblfilepath: pathlib.Path = newpdflatexsource.get_maindocument_tempfile(suffix="bbl")
        bblfile = BibTexParentTransformer.load_bib_from_bbl(newpdflatexsource=newpdflatexsource)

        bblfile_endindex = bblfile.find("\\end{thebibliography}")
        assert bblfile_endindex != -1

        bblfile_extended = bblfile[:bblfile_endindex] + parsed_bblbibitems + bblfile[bblfile_endindex:]
        bblfilepath.write_text(bblfile_extended)


