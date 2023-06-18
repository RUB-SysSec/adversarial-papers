# Crawl bibtex entries for BibTexTransformer

- Python 3
- Requirements:
	- pip install arxiv2bib
	- pip install arxiv
	- bibtexparser (should be part of our project anyway)

## 1. Step, Crawl Arxiv:
- Go to the ```crawl_arxiv_bibtex``` directory.

a) Get multiple categories at once.
- Call the following to iterate over multiple categories and to download them:
```
bash crawl.sh
```

b) Alternatively, if you want to download only a single category, just use:
```
python arxivcrawler.py "cs.CR" -m 3
```

## 2. Step, Post-Process
- use postprocess_crawled_arxiv_bibs.py
- the first step will lead to different bib files (*.bib) in the directory of the python script.
- Specify this directory as input-dir and another as output-dir.
```
python postprocess_crawled_arxiv_bibs.py --input_dir=INPUT_DIR --output_dir=OUTPUT_DIR
```
- Make sure input_dir and output_dir are different


## 3. Copy
- If result is okay, copy the bib files to <REPO-ROOT>/evaluation/problemspace/bibsources
- Make sure that there is no cached "bibsources.pck". Delete it if present.
  - However, do *not* delete "bibsources_bibtextests.pck". This file is needed for the unit tests.
- The BibTexTransformer will use the crawled bib entries if suitable.