### Get Stemming Mapping from paper corpus ###
import pickle
import typing
from nltk.stem import PorterStemmer
from pathlib import Path
import traceback
from utils.pdf_utils import get_stop_words, find_words, scrape_via_pdftotext
from typing import Set

# *Specify here the path to the corpus. All pdfs are selected within*
tpms_corpus = Path.cwd().parent.joinpath('evaluation', 'tpms_corpus')
assert tpms_corpus.exists()

# tpms_corpus = Path("/dev/shm/examples")


# Now get all pdfs and extract words, get mapping from stem to original word

def analyze_words_without_stemming(pdf_file):
    stops = get_stop_words()
    try:
        text = scrape_via_pdftotext(pdf_file)
        words = find_words(text)
        stopped_words = [w for w in words if not w in stops]
        return stopped_words
    except KeyboardInterrupt:
        return []
    except:
        print(f"\nUnexpected error while opening pdf {pdf_file}!\n {traceback.format_exc()}")
        return []

def _load_reviewer_pdf(pdf_file):
    pdf_words = analyze_words_without_stemming(pdf_file)
    return pdf_words



map_stemming_reverted: typing.Dict[str, typing.Set[str]] = {}
stemmer = PorterStemmer()

for pathobject in tpms_corpus.rglob("*.pdf"):
    # print(pathobject) # or use rglob for recursively!
    cur_words = _load_reviewer_pdf(pdf_file=pathobject)
    for w in cur_words:

        stemmed_word = stemmer.stem(word=w)
        if stemmed_word not in map_stemming_reverted:
            map_stemming_reverted[stemmed_word] = set()
        map_stemming_reverted[stemmed_word].add(w)

target_path = Path.cwd()
with open(target_path / 'map_stemming_reverted_tpms_corpus.pkl', 'wb') as f:
    pickle.dump(map_stemming_reverted, f, pickle.HIGHEST_PROTOCOL)




