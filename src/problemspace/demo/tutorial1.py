## This file shows how to use the pdflatexsource API and transformation API ##

# 1. First, we need access to the latex source of a paper, let's take an example paper from repo.
from pathlib import Path

latexpaper: Path = Path.cwd() / "problemspace" / "demo" / "unit_latex"  # make sure that the path is correct!

assert latexpaper.exists()


# 2. Now create the Python-based proxy of the latex paper, to this end, we use PdfLatexSource
from problemspace.PdfLatexSource import PdfLatexSource

originalpdflatexsource: PdfLatexSource = PdfLatexSource(latexsourcedir=latexpaper, latexmainfilename="main.tex")
print(originalpdflatexsource)  # show directory of represented latex project

# This object points to the directory of the latex paper!
# We do not want to change the original file, so let's create a copy!
workingpdflatexsource: PdfLatexSource = originalpdflatexsource.copyto()

# We have now copied the whole latex directory to a temporary dir:
print(workingpdflatexsource)  # show directory of represented latex project

# PdfLatexSource is a proxy, so if we call copyto(), the object automatically creates a new temporary dir
# If we delete it, the respective temporary dir will also be deleted!

# We can now compile the latex source too.
workingpdflatexsource.runpdflatex()

# 3. Now let's try some transformations
from problemspace.transformers.Transformer import Transformer
from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.CommentBoxAddWordTransformer import CommentBoxAddWordTransformer
from problemspace.transformers.LogSettings import LogSettings

# Let's add the word "wizard" 3x
wordsdict = {'wizard': 3}

# We need to define some settings for logging, for now, just leave it as it is.
logsettings: LogSettings = LogSettings()

# We define the transformer and a transformation state
transf: Transformer = CommentBoxAddWordTransformer(logsettings=logsettings)
transfstate: TransformationState = TransformationState(pdflatexsource=workingpdflatexsource,
                                                       original_wordsdict=wordsdict)

# Then we can apply the transformer.
newtransfstate = transf.apply_transformer(transformationstate=transfstate)

print("You will the changed PDF in {}. Open it and try to find 'wizard'".format(newtransfstate.pdflatexsource))

