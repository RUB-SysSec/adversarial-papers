import json
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

DATA_DIR = Path('/root/adversarial-papers/evaluation/corpus/large')

def find_pdfs_in_popup(link, driver):
    driver.get(link)
    time.sleep(5) # rate limit
    # remove whitespace, since sometimes the URL wraps
    html = re.sub('\s', '', driver.page_source)
    href_links = re.findall('[hH][rR][eE][fF]\s*=\s*[\'"](.+?)[\'"]', html)
    # find PDF files
    pdf_links = set([ link for link in href_links if 'pdf' in link.lower()])
    if len(pdf_links) == 0:
        return None
    else:
        return list(pdf_links)

def get_papers(scholar_link):
    # create driver
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(executable_path="/root/chromedriver", options=chrome_options)
    driver_popup = webdriver.Chrome(executable_path="/root/chromedriver", options=chrome_options)
    # get scholar profile
    driver.get(scholar_link)
    # click "show more"
    for _ in range(5):
        driver.find_element_by_xpath('//*[@id="gsc_bpf_more"]/span').click()
        time.sleep(1)
    # find paper table
    for table in driver.find_elements_by_tag_name('table'):
        table_header = table.find_element_by_tag_name('thead')
        if table_header.text == 'TITLE\nCITED BY\nYEAR':
            break
    table_body = table.find_element_by_tag_name('tbody')
    # parse table entries
    papers = []
    paper_entries = table_body.find_elements_by_class_name('gsc_a_tr')
    for paper_entry in tqdm(paper_entries, bar_format='    {l_bar}{bar:30}{r_bar}'):
        title = paper_entry.find_element_by_class_name('gsc_a_at').text
        try:
            citations = paper_entry.find_element_by_class_name('gsc_a_c').text.split()[0]
        except:
            citations = ''
        year = paper_entry.find_element_by_class_name('gsc_a_y').text
        pdf_links = find_pdfs_in_popup(paper_entry.find_element_by_class_name('gsc_a_at').get_attribute('href'), driver_popup)

        papers += [{
            'title' : title,
            'citations' : citations,
            'year' : year,
            'pdf_links' : pdf_links
        }]
    driver.close()
    return papers

if __name__ == "__main__":
    profiles_dir = DATA_DIR / "profiles"
    pc_members = json.loads(DATA_DIR.joinpath('pc.json').read_text(encoding="utf-8"))

    for pc_member, scholar_id in pc_members.items():
        link = f'https://scholar.google.com/citations?user={scholar_id}'
        print(f'[+] {pc_member}')
        out_file = profiles_dir.joinpath(pc_member.lower().replace(' ', '_').encode('ascii', 'replace').decode()).with_suffix('.json')
        if out_file.is_file():
            continue
        try:
            papers = get_papers(link)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(json.dumps(papers, indent=4))
            time.sleep(600) # rate limit
        except Exception as e:
            print(f'[!] Error {pc_member} {link}')
            import traceback
            print(traceback.format_exc())

        