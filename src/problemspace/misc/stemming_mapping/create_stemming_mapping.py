import nltk
import typing
from nltk.corpus import brown
import sys
import pickle
from pathlib import Path
from nltk.stem import PorterStemmer
from utils.pdf_utils import is_digit

try:
    brown.words()[:10]
except LookupError as e:
    print(f"Need to download dictionary. Not found on disk", file=sys.stderr)
    print(str(e), file=sys.stderr)
    nltk.download('brown')

len(brown.words())


map_stemming_reverted: typing.Dict[str, typing.Set[str]] = {}
stemmer = PorterStemmer()

for word in brown.words():
    if not is_digit(word) and len(word) > 1:  # Reject numbers and single letters

        stemmed_word = stemmer.stem(word=word)
        if stemmed_word not in map_stemming_reverted:
            map_stemming_reverted[stemmed_word] = set()
        map_stemming_reverted[stemmed_word].add(word)

# show a few examples
print("A few examples...")

print(map_stemming_reverted['attack'])
print(map_stemming_reverted['attacker']) # lookup error

print(map_stemming_reverted['evi']) # lookup error
print(map_stemming_reverted['advers']) # lookup error

target_path = Path.cwd()
with open(target_path / 'map_stemming_reverted.pkl', 'wb') as f:
    pickle.dump(map_stemming_reverted, f, pickle.HIGHEST_PROTOCOL)
