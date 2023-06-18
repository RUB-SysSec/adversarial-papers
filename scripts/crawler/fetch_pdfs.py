
import hashlib
import json
import re
import shutil
import sys
from tarfile import BLOCKSIZE
import time
from itertools import product
from pathlib import Path
from subprocess import DEVNULL, PIPE, TimeoutExpired, run
from tempfile import TemporaryDirectory
from difflib import SequenceMatcher

DATA_DIR = Path('/root/adversarial-papers/evaluation/corpus/large')
BLOCKLIST = Path('/root/adversarial-papers/scripts/fetch/blocklist.json')

class DownloadError(Exception):
    def __init__(self, reason, url):
        self.reason = reason
        super().__init__(f'{self.reason} {url}')

def fetch_pdf(urls, archives_dir):
    if not urls:
        print('[!] Failed : No Links')
        return ["No links"]
    time.sleep(3) # rate limit
    download_status = []
    for url in urls:
        with TemporaryDirectory() as tmp_dir:
            try:
                # download file
                user_agent = '"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15"'
                cmd = f'wget -U {user_agent} --no-clobber --directory-prefix={tmp_dir}  --output-document=out.pdf --no-check-certificate {url}'
                try:
                    run(cmd, timeout=10, shell=True, stderr=DEVNULL, stdout=DEVNULL, cwd=tmp_dir)
                except TimeoutExpired:
                    raise DownloadError(f'Timeout', url)
                # download succesful?
                pdf_file = Path(tmp_dir, 'out.pdf')
                if not pdf_file.is_file():
                    raise DownloadError(f'Download Error', url)
                # is pdf?
                p = run(f'file {pdf_file}', shell=True, stdout=PIPE)
                if not 'PDF document' in p.stdout.decode():
                    raise DownloadError(f"Not a PDF, {p.stdout.decode().split(':', 1)[1].strip()}",  url)
                # is usable?
                cmd = f'pdftotext {pdf_file} -'
                p = run(cmd, shell=True, stdout=PIPE, stderr=DEVNULL)
                pdf_text = p.stdout.decode()
                words = re.findall(r'(\w+)', pdf_text.lower())
                threshold_max = 25000 # exclude proceedings, dissertations, extremely long papers
                threshold_min = 2000  # exclude slides, very short papers
                if len(words) > threshold_max:
                    raise DownloadError(f"Too many words", url)
                if len(words) < threshold_min:
                    raise DownloadError(f"Too few words", url)
                # does already exist?
                md5Hash = hashlib.md5(pdf_file.read_bytes())
                pdf_hash = md5Hash.hexdigest()
                out_file = archives_dir.joinpath(f'{pdf_hash}.pdf')
                if out_file.is_file():
                    raise DownloadError(f"PDF already exists", url)
                # save in archive
                archives_dir.mkdir(exist_ok=True, parents=True)
                shutil.copyfile(pdf_file, out_file)
                print(f'[+] Success: {out_file.name}')
                download_status.append((f"Success {md5Hash.hexdigest()}"))
                break
            except DownloadError as e:
                print('[!] Failed :', e)
                download_status.append(e.reason)
    return download_status

def sort_papers(papers):
    # available years
    years = sorted({ paper['year'] for paper in papers }, reverse=True)
    # sort papers
    sorted_papers = [] 
    for year in years:
        # get paper from current year
        paper_from_year = [ paper for paper in papers if paper['year'] == year ]
        # sort by citations
        paper_from_year = sorted(paper_from_year, key=lambda p: int(p['citations']) if p['citations'] else 0, reverse=True)
        # rermove paper w/o any citation
        paper_from_year = [ paper for paper in paper_from_year if paper['citations'] ]
        # append to list
        sorted_papers += paper_from_year
    return sorted_papers

if __name__ == "__main__":

    papers_per_archive = 40

    profiles_dir = DATA_DIR / "profiles"
    archives_dir = DATA_DIR / "archives"

    if BLOCKLIST.is_file():
        submissions = [ submission for submission in json.loads(BLOCKLIST.read_text()) ]
        print(f"[+] Filter {len(submissions)} submissions from corpus\n")
    else:
        print("[+] Do not filter submissions from corpus\n")
        submissions = []

    archives_dir.mkdir(parents=True, exist_ok=True)
    for idx, reviewer_file in enumerate(profiles_dir.glob('*.json')):
        try:
            print(f'{idx:>03} {reviewer_file.stem.upper()}')
            reviewer_name = reviewer_file.stem
            reviewer_dir = archives_dir.joinpath(reviewer_name)

            if reviewer_dir.is_dir():
                print("[+] done")
                continue
            
            # get and sort papers
            papers = json.loads(reviewer_file.read_text())
            papers = sort_papers(papers)

            # download PDFs
            with TemporaryDirectory() as tmp_dir:
                download_history = []
                for paper in papers:
                    # check if paper is in submissions
                    for submission in submissions:
                        similarity = SequenceMatcher(None, submission.lower(), paper['title'].lower()).ratio()
                        if similarity > 0.85:
                            paper['download_status'] = f'Conflict with submission "{submission}" @ {similarity}'
                            print('[!] Failed :', paper['download_status'])          
                            break
                    else:
                        # otherwise download pdf
                        paper['download_status'] = fetch_pdf(paper['pdf_links'], Path(tmp_dir))
                    download_history.append(paper)
                    # found enough?
                    no_of_pdfs = len(list(Path(tmp_dir).glob('*.pdf')))
                    if no_of_pdfs == papers_per_archive:
                        break
                else:
                    print("[!] ran out of publications")

                # copy results
                shutil.copytree(tmp_dir, reviewer_dir)
                reviewer_dir.joinpath('_download_history.json').write_text(json.dumps(download_history, indent=4))

        except KeyboardInterrupt:
            break
        except: 
            pass
        print()

        # fix permissions (*hust*)
        run("chown -R 1003:1007 %s" % archives_dir, shell=True)
        run("find %s -type d -exec chmod 755 {} +" % archives_dir, shell=True)
        run("find %s -type f -exec chmod 644 {} +" % archives_dir, shell=True)
