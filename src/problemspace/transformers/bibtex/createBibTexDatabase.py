import sys
import argparse
from pathlib import Path

from problemspace.transformers.bibtex.BibTexDatabase import BibTexDatabase



if __name__ == '__main__':
    print("Next, we create the bibtex database that is needed for the BibTex Transformer.")
    parser = argparse.ArgumentParser()
    parser.add_argument('--bibtexfiles', type=Path,
                                  default=Path.home().joinpath('adversarial-papers', 'evaluation', 'problemspace', 'bibsources'))
    args = parser.parse_args()

    bibtexfiles: Path = args.bibtexfiles
    assert bibtexfiles.exists(), "{} does not exist".format(str(bibtexfiles))

    bibtexdatabasepath = bibtexfiles / "bibsources.pck"
    if bibtexdatabasepath.exists():
        print("Bibtex database already exists. I will overwrite it!", file=sys.stderr)

    bibtexdatabase = BibTexDatabase(verbose=True)
    bibtexdatabase.add_bibfiles_from_disk(bibtexfiles)
    bibtexdatabase.save_bibtexdatabase_to_pickle(targetfilepath=bibtexdatabasepath, overwrite=True)


