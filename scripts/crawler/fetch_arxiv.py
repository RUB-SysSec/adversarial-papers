import requests
from xml.dom import minidom
from subprocess import DEVNULL, PIPE, TimeoutExpired, run
from tempfile import TemporaryDirectory
from pathlib import Path
import json
import shutil

class DownloadError(Exception):
    def __init__(self, reason, url):
        self.reason = reason
        super().__init__(f'{self.reason} {url}')

def fetch_arxiv(arxiv_id, pdf_dir, pdf_source_dir):
    with TemporaryDirectory() as tmp_dir:
        try:
            # fetch links
            feed = requests.get(f'http://export.arxiv.org/api/query?id_list={arxiv_id}').text
            pdf_link = [ link.attributes['href'].value.replace('arxiv.org', 'export.arxiv.org')
                        for link in minidom.parseString(feed).getElementsByTagName('link') 
                        if 'title' in link.attributes and link.attributes['title'].value == 'pdf'][0]
            pdf_source_link = pdf_link.replace('pdf', 'e-print')

            # download pdf
            user_agent = '"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15"'
            cmd = f'wget -U {user_agent} --no-clobber --directory-prefix={tmp_dir}  --output-document=out.pdf --no-check-certificate {pdf_link}'
            try:
                run(cmd, timeout=20, shell=True, stderr=DEVNULL, stdout=DEVNULL, cwd=tmp_dir)
            except TimeoutExpired:
                raise DownloadError(f'Timeout', pdf_link)
            # download succesful?
            pdf_file = Path(tmp_dir, 'out.pdf')
            if not pdf_file.is_file():
                raise DownloadError(f'Download Error', pdf_link)
            # is pdf?
            p = run(f'file {pdf_file}', shell=True, stdout=PIPE)
            if not 'PDF document' in p.stdout.decode():
                raise DownloadError(f"Not a PDF, {p.stdout.decode().split(':', 1)[1].strip()}", pdf_link)

            # download source
            source_dir = Path(tmp_dir, 'source'); source_dir.mkdir()
            user_agent = '"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15"'
            cmd = f'wget -U {user_agent} --no-clobber --directory-prefix={tmp_dir} --output-document=out.tar.gz --no-check-certificate {pdf_source_link} && tar -xf out.tar.gz -C {source_dir}'
            try:
                run(cmd, timeout=20, shell=True, stderr=DEVNULL, stdout=DEVNULL, cwd=tmp_dir)
            except TimeoutExpired:
                raise DownloadError(f'Timeout', pdf_source_link)
            # download and extraction succesful?
            if len(list(source_dir.glob('*'))) == 0:
                raise DownloadError(f'No source code', pdf_source_link)
            
            shutil.copyfile(Path(tmp_dir, 'out.pdf'), pdf_dir.joinpath(f'{arxiv_id}.pdf'))
            shutil.copytree(Path(tmp_dir, 'source'), pdf_source_dir.joinpath(f'{arxiv_id}'))
        except DownloadError as e:
            print('[!] Failed :', e)


out_dir = Path.home().joinpath('/adversarial-papers/evaluation/submissions/oakland_22')
pdf_dir = out_dir.joinpath('pdf_arxiv'); pdf_dir.mkdir(parents=True, exist_ok=True)
pdf_source_dir = out_dir.joinpath('pdf_source'); pdf_source_dir.mkdir(parents=True, exist_ok=True)

submissions = json.loads(Path.home().joinpath('/adversarial-papers/evaluation/submissions/oakland_22/submissions.json').read_text())
for submission_name, arxiv_id in submissions.items():
    if not arxiv_id:
        continue
    if pdf_dir.joinpath(f'{arxiv_id}.pdf').is_file():
        continue
    print(f"[+] {submission_name}")
    fetch_arxiv(arxiv_id, pdf_dir, pdf_source_dir)
