# Step 3 after test_compilation_dataset
# Check if all sources in submission dataset can be parsed correctly by our latex parser

import pathlib
import sys
import traceback
from problemspace.PdfLatexSource import PdfLatexSource
from problemspace.transformers.LogSettings import LogSettings
from problemspace.transformers.CommentBoxDelWordTransformer import CommentBoxDelWordTransformer
from problemspace.transformers.ReplacementTransform import ReplacementTransformer
from problemspace.transformers.IgnoredEnvironments import IGNORED_ENVS

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


def parse_doc(doc: str):
    content_start = doc.index("\\begin{document}") + len(
        "\\begin{document}")
    content_end = doc.index("\\end{document}")
    assert content_start <= content_end

    commentboxdeltransf: ReplacementTransformer = CommentBoxDelWordTransformer(logsettings=LogSettings())
    check_within_cmd = True
    ignore_quick_math = True

    _, inside_ignored = commentboxdeltransf._find_ignored_sections(
        doc, content_start, content_end, IGNORED_ENVS,
        check_within_cmd, ignore_quick_math)


for pathobject in evaluation_directory.glob("*"):
    if pathobject.is_dir():
        dir_name = pathobject.name

        try:
            ## 1. create python-based pdf-latex-source object
            original_pdflatexsource: PdfLatexSource = PdfLatexSource(latexsourcedir=pathobject)
            ## 2. we directly copy the original project to a new directory, as we will change the latex and pdf files
            pdflatexsource: PdfLatexSource = original_pdflatexsource.copyto()
            del original_pdflatexsource  # just to ensure we do not mess up anything

            ## 3. Now check, this step should work!
            parse_doc(doc=pdflatexsource.get_main_document())

        except Exception as e:
            print(f"{dir_name} led to exception: {str(e)[:200]}", file=sys.stderr)
            # print(traceback.format_exc(), file=sys.stderr)
            print("*"*40+"\n")