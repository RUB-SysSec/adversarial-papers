import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import pdftotext


@dataclass
class Treeish:
    commit: str
    path: str

    def __hash__(self):
        return hash(hash(self.commit) + hash(self.path))


@dataclass
class FileObject:
    filepath: str
    content: str

    def __hash__(self):
        return hash(hash(self.filepath) + hash(self.content))


def get_filelist(treeish: Treeish) -> List[str]:
    if treeish.commit is None:
        cmd = ["find", treeish.path, "-type", "f"]
        print("Run cmd", cmd)

        p = subprocess.run(cmd,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL)
    else:
        cmd = [
            "git", "ls-tree", "-r", "--name-only", treeish.commit, treeish.path
        ]
        print("Run cmd", cmd)

        p = subprocess.run(cmd,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL)

    if p.returncode != 0:
        raise RuntimeError("git error")

    filepaths = sorted([f for f in p.stdout.decode("utf-8").split("\n") if f])
    return filepaths


def load_treeish(treeish: Treeish) -> List[FileObject]:
    filepaths = get_filelist(treeish)
    files = []

    if treeish.commit is None:
        for filepath in filepaths:
            print("Open file", filepath)
            with open(filepath, "rb") as f:
                files.append(FileObject(filepath=filepath, content=f.read()))
    else:
        for filepath in filepaths:
            cmd = ["git", "show", treeish.commit + ":" + filepath]
            print("Run cmd: ", cmd)

            p = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL)

            if p.returncode != 0:
                raise RuntimeError("git error")

            files.append(FileObject(filepath=filepath, content=p.stdout))

    return files


def copy_files_to_folder(file_list, tmp_dir):
    for file in file_list:
        relative_path, filename = os.path.split(file.filepath)

        tmp_path = Path(tmp_dir, relative_path)
        tmp_path.mkdir(parents=True, exist_ok=True)

        full_path = Path(tmp_path, filename)

        with open(full_path, "wb") as f:
            f.write(file.content)


def run_pdflatex(path):
    cmd = ['pdflatex', '-interaction', 'nonstopmode', "main.tex"]
    print("Run cmd", cmd, "in", path)

    p = subprocess.run(cmd,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       shell=False,
                       timeout=120,
                       cwd=str(path))

    output, err = p.stdout, p.stderr

    if p.returncode != 0:
        print("WARNING: Non-zero returncode for pdflatex")


def run_pdftotext(path, pdfname="main.pdf"):
    print("Run pdftotext on", path, pdfname)
    with open(Path(path, pdfname), "rb") as f:
        pdf = pdftotext.PDF(f)

    return "\n\n".join(pdf)


def run_extraction(treeish: Treeish):
    # load iffalse version of treeish (from git)
    file_list = load_treeish(treeish)

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir, treeish.path)

        copy_files_to_folder(file_list, tmp_dir)

        run_pdflatex(tmp_path)
        return run_pdftotext(tmp_path)


def main(treeish0: Treeish, treeish1: Treeish):
    pdf_content0 = run_extraction(treeish0)
    pdf_content1 = run_extraction(treeish1)

    if pdf_content0 == pdf_content1:
        print("*********************************")
        print("*********************************")
        print("Success: Both files are identical")
        print("*********************************")
        print("*********************************")
        print()
        sys.exit(0)
    else:
        print("!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!")
        print("ERROR: PDF files differ")
        print("!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!")
        print()
        sys.exit(1)

    # TODO:
    # - Copy files to /tmp
    # - Run pdflatex in each folder containing main.tex
    # - Use pdf2tex to extract text from pdf file
    # - Compare outputs (should be equal since we only remove iffalse blocks)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python compare.py [commit0] [path0] [commit1] [path1]")
        sys.exit(0)

    commit0, path0, commit1, path1 = sys.argv[1:]

    print(f"Comparing {commit0}:{path0} with {commit1}:{path1}")

    if commit0 == "None":
        commit0 = None

    if commit1 == "None":
        commit1 = None

    treeish0 = Treeish(commit=commit0, path=path0)
    treeish1 = Treeish(commit=commit1, path=path1)

    main(treeish0, treeish1)
