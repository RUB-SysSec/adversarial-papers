# Step 2, postprocess arxiv bibs, that is, only keep necessary fields.
# Call via: python postprocess_crawled_arxiv_bibs.py --input_dir=INPUT_DIR --output_dir=OUTPUT_DIR
# MAKE SURE THAT INPUT_DIR and OUTPUT_DIR is different!

import pathlib
import argparse
import sys
import bibtexparser
from bibtexparser.bwriter import BibTexWriter


def postprocess(input_dir: pathlib.Path, output_dir: pathlib.Path):
    for inputbibfile in input_dir.glob("*.bib"):

        assert inputbibfile.exists(), f"bib file {inputbibfile} does not exist"
        with open(inputbibfile, "r") as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)

        arxiv_keys = ["title", "author", "eprint", "archiveprefix", "year", "ENTRYTYPE"]
        newbibfile = ""
        for bibtex_entry in bib_database.entries:
            if not all(arxiv_key in bibtex_entry.keys() for arxiv_key in arxiv_keys):
                print(f"For {bibtex_entry['ID']} key is missing", file=sys.stderr)
                continue

            minimalentry = {}
            for k, v in bibtex_entry.items():
                if k in ['ENTRYTYPE', 'ID', 'author', 'title', 'year']:
                    minimalentry[k] = v
            minimalentry['journal'] = f"ArXiv:{bibtex_entry['eprint']}"

            writerb = BibTexWriter()
            newentry = writerb._entry_to_bibtex(minimalentry)
            newbibfile += newentry

        outputbibfile = output_dir / inputbibfile.name
        outputbibfile.write_text(newbibfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", help="input directory with bib files. All *.bib will be processed.",
                        type=pathlib.Path)
    parser.add_argument("--output_dir", help="output directory with bib files", type=pathlib.Path)
    args = parser.parse_args()

    error_msg = "Error: input dir == output dir. Files will be overwritten. Please change outputdir"
    assert args.input_dir != args.output_dir, error_msg
    postprocess(input_dir=args.input_dir, output_dir=args.output_dir)
