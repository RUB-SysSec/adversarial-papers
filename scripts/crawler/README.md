## Container for crawling with all dependencies (i.e., selenium)

In this directory we release all of our crawling scripts used for crawling Google Scholar in the end of 2022. 

We provide a docker container with the necessary environment, which can be build with 
```
docker build -t fetch .
```

In case there is an error like `E: Version '105.0.5195.102-0ubuntu0.18.04.1' for 'chromium-browser' was not found` you need to bump the version of the the chromium browser and driver as these are regularly deprecated. We used chromium in version `105.0.5195.102` but more recent versions should work as well. 

After successfully building the container, crawling is a three step process:

First, we collect a list of reviewers with their respective Google Scholar user id. This is summarized in a file `pc.json` which has the following format:

```
{
    "Researcher 1": "XXXXXXXXXXXX",
    "Researcher 2": "XXXXXXXXXXXX",
    "Researcher 3": "XXXXXXXXXXXX",
    ...
}
```

with `XXXXXXXXXXXX` being the user id as in `https://scholar.google.de/citations?user=XXXXXXXXXXXX`. In `evaluation/corpus` we release the files from all copora used in our experiments. 

Second, we crawl Google Scholar to get a list of publications of each researcher from their profile. Therefore, we use the `fetch_scholar_profiles.py` script. It expect as input the directory of the corpus. Adjust the `DATA_DIR` variable in the script accordingly.

```
docker run -v ~/adversarial-papers/:/root/adversarial-papers --rm -it fetch
clear; python3 fetch_scholar_profiles.py
```

Finally, we use the `fetch_pdfs` script to download the actual PDF files:
```
docker run -v ~/adversarial-papers/:/root/adversarial-papers --rm -it fetch
clear; python3 fetch_pdfs.py
```

Again, this script expects the directory to the corpus as input. As an additional input, it is possible to pass a list with paper titles that should be excluded from the reviewer archives (see `blocklist.json`). This is used to avoid any target papers to be included in the corpus.