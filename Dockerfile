FROM ubuntu:20.04

RUN apt update &&\
    apt upgrade -y

RUN apt update &&\
    apt install -y curl python3-pip git tmux htop psmisc

# pdftotext
RUN apt update \
    && apt install -y poppler-utils

# latex
ENV DEBIAN_FRONTEND='noninteractive'
RUN    apt update \
    && apt install -y texlive-full

WORKDIR /root
ADD . /root/adversarial-papers

# install requirements
WORKDIR /root/adversarial-papers
RUN pip install -r requirements.txt

# init problem space requirements
RUN python3 -m spacy download en_core_web_sm
RUN python3 -c "from transformers import pipeline, set_seed; generator = pipeline('text-generation', model='gpt2')"
RUN PYTHONPATH=/root/adversarial-papers/src python3 /root/adversarial-papers/src/problemspace/transformers/bibtex/createBibTexDatabase.py --bibtexfiles /root/adversarial-papers/evaluation/problemspace/bibsources/

# unit tests (requires problemspace models in 'evaluation/problemspace')
# WORKDIR /root/adversarial-papers/src
# RUN PYTHONPATH=/root/adversarial-papers/src python3 -m unittest discover problemspace/tests/unittesting/

WORKDIR /root/adversarial-papers