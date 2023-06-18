# Dataset Preparation

## A. Preprocess dataset
- First, we need to run latexpand to remove comments and to resolve all includes, so that
we have one main file with all content. We also want to identify the main latex file of each arxiv
directory. We rename it to main.tex simply.
- Go to ```preprocess_dataset``` to this end (contains its own readme.txt)

## B. Test if compiling
### Compile Check
- Second, go to ```test_compilation_dataset``` and run `test_compilation_dataset.py`
- Check where error occurs
- It can happen for some arxiv submissions that latexpand creates a broken latex file.
- In this case, revert it to original version and resolve includes manually
- Do not forget to remove comments (e.g. arxiv-latex-cleaner might help you)
- But if e.g. code listings causes problems with latexpand, then arxiv-latex-cleaner
will probably also have problems (by not correctly differentiating % in code listings and latex).
- Then, you have to do that manually.

- In our dataset, 1912.11118 and 1908.03296 led to latexpand errors, had to resolve manually
- For 1909.01838, in first run, we got a warning that font metrics... just re-run again. 

### Parser Check
- Third, go to ```test_compilation_dataset``` and run `test_latexparser_dataset.py`
- Check where error occurs

## C Some further post-processing
1. We need to remove all if-(else) branches. 
- Problem is that we may add some content to a branch in latex that is not compiled. The attack will not work in 
this case.
- https://riptutorial.com/latex/example/28656/if-statements
- As removing such branches is quite difficult, we only provide a bash script to identify such cases in the dataset.
- Then, you can remove the cases manually, and afterwards you can check that your changes do not have an impact on 
the pdf by comparing the pdf content before and after your manual removal
- Go to postprocess_dataset/ifelse
2. Look out for { ... } brackets just to enclose the entire document. This can lead to problems. # TODO 

## D. Work with it
Now we can work with dataset.
