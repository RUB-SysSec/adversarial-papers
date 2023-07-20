FROM ubuntu:18.04

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN    apt update \
    && apt upgrade -y \
    && apt install -y locales

# setup selenium
WORKDIR /root
RUN apt update \
    && apt install -y wget unzip chromium-browser=112.0.5615.49-0ubuntu0.18.04.1 \
    && wget https://chromedriver.storage.googleapis.com/112.0.5615.49/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && rm chromedriver_linux64.zip \
    && apt install -y python3 python3-pip \
    && pip3 install selenium

RUN apt install -y python3 python3-pip \
    && apt install -y poppler-utils \
    && pip3 install tqdm pypdf2

WORKDIR /root/adversarial-papers/scripts/crawler