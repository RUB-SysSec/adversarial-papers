# 1. Step, crawl bibtex sources for bibtex parser
# https://pypi.org/project/arxiv/
# https://arxiv.org/help/api/user-manual
### https://arxiv.org/help/api/user-manual#query_details
# https://pypi.org/project/arxiv2bib/

import arxiv
import argparse
import subprocess


class Crawler:
    def __init__(self, sbjcat, max_res=10):
        self.cat = sbjcat
        self.max_results = max_res

    def crawl(self):
        search = arxiv.Search(
            query="cat:" + str(self.cat),
            max_results=int(self.max_results),
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        cmd = ['arxiv2bib']
        try:
            for result in search.get():
                arxiv_id = str(result.entry_id.split("/")[-1])
                cmd.append(arxiv_id)
        except (AttributeError, KeyError):
            pass
        # print(cmd)
        print("paper count: {} out of {}".format(len(cmd) - 1, self.max_results))
        bibTex = ""
        nr_lists = int((len(cmd) - 1) / 500)
        if nr_lists * 500 < len(cmd) - 1:
            nr_lists += 1
        print(nr_lists)

        try:
            start = 1
            end = 501
            for i in range(nr_lists):
                request = []
                request.append(cmd[0])
                request += cmd[start:end]
                print("request count: {}".format(len(request) - 1))
                bibTex += str(subprocess.check_output(request).decode('utf-8'))
                start += 500
                end += 500
        except subprocess.CalledProcessError:
            pass
        filename = str(self.cat.replace(".", "")) + ".bib"
        with open(filename, "w") as f:
            f.write(bibTex)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("SUBJECT_CATEGORY",
                        help="category in which to search for paper, e.g. \"cs.CR\".", type=str)
    parser.add_argument("-m", "--max_results", help="maximum number of required results.",
                        type=int, metavar="INT", default=10)
    args = parser.parse_args()

    Crawler(args.SUBJECT_CATEGORY, args.max_results).crawl()
