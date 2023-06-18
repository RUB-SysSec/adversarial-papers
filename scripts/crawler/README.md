
Container for crawling with all dependencies (i.e., selenium)

Build with
```
docker build -t fetch .
```

Run with
```
docker run -v ~/adversarial-papers/:/root/adversarial-papers --rm -it fetch
clear; python3 fetch_pdfs.py
```