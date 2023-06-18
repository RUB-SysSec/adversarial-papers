import typing
import random
import copy
from nltk.stem import PorterStemmer

from utils.pdf_utils import analyze_words_from_string

from problemspace.transformers.LogSettings import LogSettings
from problemspace.exceptions.TransformerException import TransformerException
from problemspace.transformers.bibtex.BibTexDatabase import BibTexDatabase
from problemspace.transformers.bibtex.BibTexElementKeyworded import BibTexElementKeyworded
from problemspace.transformers.bibtex.BibTexElement import BibTexElement
from problemspace.transformers.bibtex.BibTexParentTransformer import BibTexParentTransformer
from problemspace.transformers.TransformationState import TransformationState
from problemspace.transformers.FeatureDelta import FeatureDelta


class FakeBibTexTransformer(BibTexParentTransformer):
    """
    It takes a few keywords and inserts these keywords into an exisiting paper.

    This can be more helpful if we do not have any paper in the bibtex dataset that contain the keywords.
    However, this transformer should be used with care and not too often.

    With smart_keyword_selection = True, we first try to add keywords that are not present in bibliography.
    If we do not find enough keywords (less than 'maximum_keywords_per_added_paper'),
    we use keywords that are present in the bibliography. But if we break up with smart_keyword_selection = True
    if we find no keywords that are not present in bibliography. In this case, the normal BibTexTransformer
    may make more sense to be used.
    """

    def __init__(self,
                 bibtexdatabase: BibTexDatabase,
                 maxpapers: int,
                 seed: int,
                 logsettings: LogSettings,
                 stemmer=None):
        """
        :param bibtexdatabase: bibtexdatabase, which contains a list of databases
        :param maxpapers: maximum number of modified papers that are added to bibliography
        :param seed: seed for random year generation
        :param logsettings, # TODO implement debug-coloring
        :param stemmer: can be None
        """
        super().__init__(bibtexdatabase=bibtexdatabase, logsettings=logsettings)

        self.maxpapers: int = maxpapers
        self.random = random.Random(seed)

        # threshold for fuzzy string matching to detect if a found bibtex element is already present in paper:
        self.threshold_fuzzy_matching: int = 95

        # maximum number of keywords that can be inserted into a random paper
        self.maximum_keywords_per_added_paper = 3
        # minimum number of words in a paper title where we add keywords
        self.minimum_paper_title_length = 3

        # Keywords that are not present in dataset are tried first / have a higher priority to be added
        self.smart_keyword_selection = True

        self.stemmer = stemmer

    def _build_stemmer(self):
        if self.stemmer is None:
            return PorterStemmer()
        else:
            return self.stemmer

    # @Overwritten
    def _transform(self, transformationstate: TransformationState) -> FeatureDelta:
        maindoc: str = transformationstate.pdflatexsource.get_main_document()
        stemmer = self._build_stemmer()
        current_wordsdict = copy.deepcopy(transformationstate.current_wordsdict)

        # 1. get bib information
        isbibsectioninpaper, bibstartindex = self.is_bib_in_paper(maindoc=maindoc)
        if isbibsectioninpaper is True:
            bibtext = BibTexParentTransformer.load_bib_from_paper(maindoc=maindoc, bibstartindex=bibstartindex)
        else:
            bibtext = BibTexParentTransformer.load_bib_from_bbl(newpdflatexsource=transformationstate.pdflatexsource)

        # 2.1 Create suitable bibtex elements
        bibtexelemstoadd: typing.List[BibTexElementKeyworded] = []
        for ix in range(self.maxpapers):
            if all(x <= 0 for x in current_wordsdict.values()):
                break

            keywords_to_be_added = self._get_keywords_to_be_added(current_wordsdict=current_wordsdict,
                                                                  stemmer=stemmer)
            if len(keywords_to_be_added) == 0:
                break

            new_bibtex_entry: BibTexElementKeyworded = self.__modify_existing_bibtex_entry(
                keywords_to_be_added=keywords_to_be_added,
                curbib=bibtext)

            bibtexelemstoadd.append(new_bibtex_entry)
            for keyword in new_bibtex_entry.keywords:
                current_wordsdict[keyword] -= 1

        # 2.2 If no suitable entries were found, we stop here!
        if len(bibtexelemstoadd) == 0:
            self.printlogdebug(f"        > FakeBibTexTransformer: Abort. Didn't find bibtex entry for keyword list")
            return FeatureDelta()

        # 3. Now manipulate file
        self.change_bibliography(maindoc=maindoc,
                                 isbibsectioninpaper=isbibsectioninpaper,
                                 bibstartindex=bibstartindex,
                                 transformationstate=transformationstate,
                                 bibtexelemstoadd=bibtexelemstoadd)

        # 4. Prepare output
        feature_delta: FeatureDelta = FeatureDelta()
        for keyword, original_value in transformationstate.current_wordsdict.items():
            if abs(original_value - current_wordsdict[keyword]) > 0:
                feature_delta.changes[keyword] = original_value - current_wordsdict[keyword]

        return feature_delta


    def _get_keywords_to_be_added(self, current_wordsdict: dict, stemmer) -> typing.List[str]:

        added_keywords: typing.List[str] = []
        suitable_keywords: typing.List[str] = []
        if self.smart_keyword_selection is True:
            # If true, we use words that would not be added by BibTexTransformer

            remaining_words = []
            for keyword, value in current_wordsdict.items():
                if value > 0:
                    if len(keyword) > 3:  # and value > 0:
                        bibstoadd: typing.List[BibTexElement] = self.bibtexdatabase.search_string(
                            keyword=keyword,
                            fields=BibTexDatabase.get_stemmed_fields_of_minimal_bibtex_entry())  # ["author_stemmed"])
                        if len(bibstoadd) == 0:
                            suitable_keywords.append(keyword)  # no paper with keyword found, so let's try it here
                        else:
                            remaining_words.append(keyword)
                    else:
                        suitable_keywords.append(keyword)  # too short for bibtex transformer, let's try it here

            # Shuffle in-place, mitigates that we add the same keywords when adding multiple papers
            self.random.shuffle(suitable_keywords)

            for keyword in suitable_keywords:
                if len(added_keywords) >= self.maximum_keywords_per_added_paper:
                    break
                # we should only add words that do not have a different stem if stemmed again
                if stemmer.stem(keyword) == keyword:
                    added_keywords.append(keyword)

            if (len(added_keywords) == 0) or (len(added_keywords) == self.maximum_keywords_per_added_paper):
                # if no keyword found or maxmimum number found, we can break up
                return added_keywords

            # But if we found a few, but could add more,
            # let's fill it with words that could be added by BibTexTransformer
            self.random.shuffle(remaining_words)
            for keyword in remaining_words:
                if len(added_keywords) >= self.maximum_keywords_per_added_paper:
                    break
                if stemmer.stem(keyword) == keyword:
                    added_keywords.append(keyword)

        else:
            for keyword, value in current_wordsdict.items():
                if len(added_keywords) >= self.maximum_keywords_per_added_paper:
                    break

                # we can only add bibtex elements with value > 0 AND
                # we should only add words that do not have a different stem if stemmed again
                if value > 0 and stemmer.stem(keyword) == keyword:
                    added_keywords.append(keyword)

        return added_keywords

    def __modify_existing_bibtex_entry(self, keywords_to_be_added: list, curbib: str) \
            -> BibTexElementKeyworded:
        """
        Modify an existing paper so that it includes the keywords in its title
        :param keywords_to_be_added: target changes
        :param curbib: current bib information
        :return: a modified bibtex element
        """

        # Choose random library & paper
        # We assume that 50 trials should be enough to find one that is not present in paper
        for i in range(50):
            if len(self.bibtexdatabase.bibtex_databases) == 0:
                raise TransformerException("Bibtex database is empty")
            randlib = self.random.randint(0, len(self.bibtexdatabase.bibtex_databases)-1)
            if len(self.bibtexdatabase.bibtex_databases[randlib].entries) >= 1:
                randpap = self.random.randint(0, len(self.bibtexdatabase.bibtex_databases[randlib].entries)-1)

                chosen_paper = copy.deepcopy(self.bibtexdatabase.bibtex_databases[randlib].entries[randpap])
                if self.check_paper_present(curtitle=chosen_paper['title'], curbib=curbib,
                                            threshold_fuzzy_matching=self.threshold_fuzzy_matching) is False:
                    try:
                        new_paper = self.__insert_keywords_into_bibtex_element(
                            chosen_paper=chosen_paper,
                            keywords_to_be_added=keywords_to_be_added)
                        return new_paper
                    except TransformerException as e:
                        self.printlogerr(msg=str(e))

        # if 50 trials are not enough, really unlikely, throw exception
        raise TransformerException("50 Trials to find random paper. Not successful. "
                                   "Check what is happening. Consider increasing the number of trials")

    def __insert_keywords_into_bibtex_element(self, chosen_paper: dict, keywords_to_be_added: list) \
            -> BibTexElementKeyworded:

        # Add keywords into title at random locations
        current_title: typing.List[str] = chosen_paper['title'].split()

        if len(current_title) <= self.minimum_paper_title_length:
            raise TransformerException("Paper's title is not long enough")

        insertion_position = self.random.randint(a=1, b=len(current_title))
        new_title = current_title[:insertion_position] + keywords_to_be_added + current_title[insertion_position:]

        chosen_paper['title'] = " ".join(new_title)
        chosen_paper['title_stemmed'] = " ".join(analyze_words_from_string(text=chosen_paper['title']))

        bibtexelement = BibTexElementKeyworded(fields=chosen_paper,
                                               keywords=set(keywords_to_be_added),
                                               uniqueid=chosen_paper['ID'])

        return bibtexelement
