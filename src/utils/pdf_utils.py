
import re
import traceback
from pathlib import Path
from subprocess import DEVNULL, PIPE, run

from nltk.stem.porter import PorterStemmer

######################################################
# 
#   Text analysis routines
#
######################################################

# List from: http://www.lextek.com/manuals/onix/stopwords1.html
def get_stop_words(): 
    return set([\
        "a", "about", "above", "across", "after", "again", "against",
        "all", "almost", "alone", "along", "already", "also", "although",
        "always", "among", "an", "and", "another", "any", "anybody",
        "anyone", "anything", "anywhere", "are", "area", "areas", "around",
        "as", "ask", "asked", "asking", "asks", "at", "away", "b", "back",
        "backed", "backing", "backs", "be", "became", "because", "become",
        "becomes", "been", "before", "began", "behind", "being", "beings",
        "best", "better", "between", "big", "both", "but", "by", "c",
        "came", "can", "cannot", "case", "cases", "certain", "certainly",
        "clear", "clearly", "come", "could", "d", "did", "differ",
        "different", "differently", "do", "does", "done", "down", "down",
        "downed", "downing", "downs", "during", "e", "each", "early",
        "either", "end", "ended", "ending", "ends", "enough", "even",
        "evenly", "ever", "every", "everybody", "everyone", "everything",
        "everywhere", "f", "face", "faces", "fact", "facts", "far", "felt",
        "few", "find", "finds", "first", "for", "four", "from", "full",
        "fully", "further", "furthered", "furthering", "furthers", "g",
        "gave", "general", "generally", "get", "gets", "give", "given",
        "gives", "go", "going", "good", "goods", "got", "great", "greater",
        "greatest", "group", "grouped", "grouping", "groups", "h", "had",
        "has", "have", "having", "he", "her", "here", "herself", "high",
        "high", "high", "higher", "highest", "him", "himself", "his",
        "how", "however", "i", "if", "important", "in", "interest",
        "interested", "interesting", "interests", "into", "is", "it",
        "its", "itself", "j", "just", "k", "keep", "keeps", "kind", "knew",
        "know", "known", "knows", "l", "large", "largely", "last", "later",
        "latest", "least", "less", "let", "lets", "like", "likely", "long",
        "longer", "longest", "m", "made", "make", "making", "man", "many",
        "may", "me", "member", "members", "men", "might", "more", "most",
        "mostly", "mr", "mrs", "much", "must", "my", "myself", "n",
        "necessary", "need", "needed", "needing", "needs", "never", "new",
        "new", "newer", "newest", "next", "no", "nobody", "non", "noone",
        "not", "nothing", "now", "nowhere", "number", "numbers", "o", "of",
        "off", "often", "old", "older", "oldest", "on", "once", "one",
        "only", "open", "opened", "opening", "opens", "or", "order",
        "ordered", "ordering", "orders", "other", "others", "our", "out",
        "over", "p", "part", "parted", "parting", "parts", "per",
        "perhaps", "place", "places", "point", "pointed", "pointing",
        "points", "possible", "present", "presented", "presenting",
        "presents", "problem", "problems", "put", "puts", "q", "quite",
        "r", "rather", "really", "right", "right", "room", "rooms", "s",
        "said", "same", "saw", "say", "says", "second", "seconds", "see",
        "seem", "seemed", "seeming", "seems", "sees", "several", "shall",
        "she", "should", "show", "showed", "showing", "shows", "side",
        "sides", "since", "small", "smaller", "smallest", "so", "some",
        "somebody", "someone", "something", "somewhere", "state", "states",
        "still", "still", "such", "sure", "t", "take", "taken", "than",
        "that", "the", "their", "them", "then", "there", "therefore",
        "these", "they", "thing", "things", "think", "thinks", "this",
        "those", "though", "thought", "thoughts", "three", "through",
        "thus", "to", "today", "together", "too", "took", "toward", "turn",
        "turned", "turning", "turns", "two", "u", "under", "until", "up",
        "upon", "us", "use", "used", "uses", "v", "very", "w", "want",
        "wanted", "wanting", "wants", "was", "way", "ways", "we", "well",
        "wells", "went", "were", "what", "when", "where", "whether", "which",
        "while", "who", "whole", "whose", "why", "will", "with", "within",
        "without", "work", "worked", "working", "works", "would", "x", "y",
        "year", "years", "yet", "you", "young", "younger", "youngest", "your",
        "yours", "z"
        ])

def is_digit(word):
    try:
        int(word)
        return True
    except ValueError:
        return False

def find_words(string):
    #words = page.lower().split()
    words = re.findall(r'(\w+)', string.lower())
    new_words = []
    for w in words:
        if not is_digit(w) and len(w) > 1:  # Reject numbers and single letters
            new_words.append(w)
    return new_words

def scrape_via_pdftotext(pdf_file):
    p = run(f'pdftotext {pdf_file} -', shell=True, stdout=PIPE, stderr=DEVNULL)
    return p.stdout.decode()

def analyze_words(pdf_file):
    stops = get_stop_words()
    p_stemmer = PorterStemmer()
    try:
        text = scrape_via_pdftotext(pdf_file)
        words = find_words(text)
        stopped_words = [w for w in words if not w in stops]
        stemmed_words = [p_stemmer.stem(w) for w in stopped_words]
        return stemmed_words
    except KeyboardInterrupt:
        return []
    except:
        print(f"\nUnexpected error while opening pdf {pdf_file}!\n {traceback.format_exc()}")
        return []

def analyze_words_from_string(text):
    """
    Equivalent feature extraction to analyze_words, but directly with text input instead of pdf-file path
    :param text: text input
    :return: list of used words/features
    """
    stops = get_stop_words()
    p_stemmer = PorterStemmer()
    words = find_words(text)
    stopped_words = [w for w in words if not w in stops]
    stemmed_words = [p_stemmer.stem(w) for w in stopped_words]
    return stemmed_words
