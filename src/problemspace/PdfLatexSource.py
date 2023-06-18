import pathlib
import shutil
import subprocess
import sys
import tempfile
import typing

from problemspace.exceptions.PdfLatexException import PdfLatexException


class PdfLatexSource:
    """
    This class is a proxy between the latex source of a paper on the disk and the python world here.
    All modifications to the tex file should run over this class.
    """

    def __init__(self,
                 latexsourcedir: pathlib.Path,
                 latexmainfilename: str = "main.tex",
                 tempdir: typing.Optional[tempfile.TemporaryDirectory] = None):
        """
        Init proxy.
        :param latexsourcedir: directory where latex project is located
        :param latexmainfilename: the name of the main file of the paper, e.g. main.tex
        :param tempdir: if given, it means that the source of the paper is within a temporary directory,
        and if this python object is deleted, then the temporary directory will also be cleaned.
        """

        if not latexsourcedir.exists():
            raise ValueError("Path {} does not exist".format(latexsourcedir))

        latexmainfile: pathlib.Path = latexsourcedir / latexmainfilename
        if not latexmainfile.exists():
            raise ValueError("Main file {} does not exist".format(latexmainfile))

        self._latexsourcedir: pathlib.Path = latexsourcedir
        self._latexmainfilename: str = latexmainfilename


        self.tempdir: typing.Optional[tempfile.TemporaryDirectory] = None
        if tempdir is not None:
            self.tempdir = tempdir

        self._maindoc = self._read_latex()

    def __del__(self):
        if self.tempdir is not None:
            self.tempdir.cleanup()

    def __str__(self):
        return str(self._latexsourcedir) + " " + str(self._latexmainfilename)

    def _read_latex(self) -> str:
        maindoc: str = (self._latexsourcedir / self._latexmainfilename).read_text()
        return maindoc

    def get_main_document(self) -> str:
        return self._maindoc

    def save_latex(self, newmaindoc: str) -> None:
        """
        Update tex document on disk
        :param newmaindoc: new main document
        """
        with open(self._latexsourcedir / self._latexmainfilename, 'w') as f:
            f.write(newmaindoc)

        # update python version of tex document
        self._maindoc = self._read_latex()

    def copyto(self) -> 'PdfLatexSource':
        """
        Create a copy of this object (includes copying the latex project on the disk to a temporary directory).
        :return: copy of current PdfLatexSource object.
        """
        tempdir = tempfile.TemporaryDirectory()
        newlatexsourcedir: pathlib.Path = pathlib.Path(tempdir.name)

        shutil.copytree(self._latexsourcedir, newlatexsourcedir / self._latexsourcedir.name)
        newpdflatexsource: PdfLatexSource = PdfLatexSource(latexsourcedir=newlatexsourcedir / self._latexsourcedir.name,
                                                           latexmainfilename=self._latexmainfilename,
                                                           tempdir=tempdir)
        return newpdflatexsource

    def copy_project_for_debugging(self, targetdir: pathlib.Path):
        newlatexsourcedir = targetdir
        shutil.copytree(self._latexsourcedir, newlatexsourcedir / self._latexsourcedir.name)
        newpdflatexsource: PdfLatexSource = PdfLatexSource(latexsourcedir=newlatexsourcedir / self._latexsourcedir.name,
                                                           latexmainfilename=self._latexmainfilename,
                                                           tempdir=None)
        return newpdflatexsource


    def runpdflatex(self) -> None:
        """
        Compile latex document on the disk.
        """

        try:
            cmd = ['pdflatex', '-interaction', 'nonstopmode', self._latexmainfilename]
            for i in range(2):  # run twice for pdflatex due to references, ...
                p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, timeout=600,
                                   cwd=str(self._latexsourcedir))
                output, err = p.stdout, p.stderr
                # if err != b'':
                # 'mismatch between font type and embedded font', for example, causes an uncritical stderr output.
                # That's why we do not raise an exception. We check for errors with returncode.
                # If you like, you can show a warning here.
                #     print("Pdflatex stderr (may only be a warning): " + str(err), file=sys.stderr)
                if not p.returncode == 0:
                    raise PdfLatexException(
                        f'Pdflatex: Executing error {p.returncode} with command: {" ".join(cmd)}')

        finally:
            pass

    def runbibtex(self) -> None:
        try:
            cmd = ['bibtex', pathlib.Path(self._latexmainfilename).stem + ".aux"]
            for i in range(1):  # run twice for pdflatex due to references, ...
                p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, timeout=600,
                                   cwd=str(self._latexsourcedir))
                output, err = p.stdout, p.stderr
                if err != b'':
                    raise PdfLatexException(
                        "Bibtex: Error in stderr:" + str(err))  # actually was never the case, but just in case
                if not p.returncode == 0:
                    raise PdfLatexException(
                        'Bibtex: Executing error {} with command: {}'.format(p.returncode, ' '.join(cmd)))

        finally:
            pass

    def get_filepath_in_dir(self, filename: str) -> pathlib.Path:
        """
        Get the file path to a file with name filename in the current latex dir.
        Let's assume we want to create a new attack.bib file in latex dir, then call this method with
        get_filepath_in_dir(filename="attack.bib") to get a pathlib.Path object to "/.../latexdir/attack.bib".
        :param filename: file name
        :return: a path to file
        """
        return self._latexsourcedir / filename

    def get_maindocument_tempfile(self, suffix: str) -> pathlib.Path:
        """
        Get the file path to a temporary object of the latex document. Let's assume we want to read
        the bbl content of the main file of the paper. Then call "get_maindocument_tempfile(suffix="bbl")
        :param suffix: suffix of temporary object
        :return: a path to file
        """
        return self._latexsourcedir / pathlib.Path(pathlib.Path(self._latexmainfilename).stem + "." + suffix)

    def get_maindocument_pdf_path(self) -> pathlib.Path:
        """
        Get the file path to the PDF of the latex document
        :return:
        """
        return self.get_maindocument_tempfile(suffix="pdf")

    @staticmethod
    def get_pdf_from_source(latex_source_dir, latex_main_filename):
        """
        Compiles the given latex source and return the path to the PDF.
        :return: (PdfLatexSource, path to compiled PDF)
        """
        # import source
        original_pdflatexsource: PdfLatexSource = PdfLatexSource(latexsourcedir=latex_source_dir,
                                                                 latexmainfilename=latex_main_filename)
        # copy source to temp dir
        pdflatexsource: PdfLatexSource = original_pdflatexsource.copyto()
        del original_pdflatexsource # just to ensure we do not mess up anything
        # compile
        pdflatexsource.runpdflatex()
        # return path to PDF
        return pdflatexsource, pdflatexsource.get_maindocument_pdf_path()
        
