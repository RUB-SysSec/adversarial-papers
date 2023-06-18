# Step 2 after preprocess_dataset
# Check if all sources in targetdir can be loaded into python and be compiled with pdflatex

import pathlib
from problemspace.PdfLatexSource import PdfLatexSource

# A. Settings
use_small_test_set: bool = False # if true, we only use three example papers
dataset_name: str = ["usenix_20", "oakland_22"][1]

# B. Check dataset
if use_small_test_set:
    evaluation_directory: pathlib.Path = pathlib.Path.cwd().parent / "evaluation" / "submissions" / "examples"
else:
    evaluation_directory: pathlib.Path = pathlib.Path.cwd().parent / "evaluation" / "submissions" / dataset_name / "arxiv-sources" / "submissions_latexpanded"
print(f"I'll test everything on {evaluation_directory}")

if not evaluation_directory.exists():
    raise Exception(f"Directory {evaluation_directory} does not exist")

for pathobject in evaluation_directory.glob("*"):
    if pathobject.is_dir():
        dir_name = pathobject.name

        try:
            ## 1. create python-based pdf-latex-source object
            original_pdflatexsource: PdfLatexSource = PdfLatexSource(latexsourcedir=pathobject)
            ## 2. we directly copy the original project to a new directory, as we will change the latex and pdf files
            pdflatexsource: PdfLatexSource = original_pdflatexsource.copyto()
            del original_pdflatexsource  # just to ensure we do not mess up anything

            ## 3. Let us compile the latex sources to get a PDF
            pdflatexsource.runpdflatex()
            # print(f"{dir_name} succeeded to compile.")

        except Exception as e:
            print(f"{dir_name} led to exception: {str(e)}")
