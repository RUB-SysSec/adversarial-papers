# Synonym Transformations

This is a simple implementation of a text transformer that replaces
synonyms using a word embedding.  The implementation supports training
a word embedding from a text corpus and applying the embedding for
transforming a set of words to synonyms. This transformation supports
the removal as well as the addition of words.

## Available Embeddings

The directory `models` contains two large word embeddings computed on a
collection of security paper submissions.  One embedding is computed
on tokenized sentences, while the other involves additional stemming of the
tokens.  Further details of the preprocessing and training can be derived
from the configuration files `config-*.yml`.

## Training and Application

The implementation is super simple. It can be used directly from the
command-line, although direct interfacing with the code is likely far
more efficient.

All essential configuration options are specified in the file
`config-*.yml`. Some of the options can be overwritten with
command-line switched, if necessary. The embedding is trained by
simply running

    python ./synonyms.py train

The training process involves only two files: a corpus of raw text
provided by the command-line option `--corpus` and the resulting model
file defined by `--model`. Both options can be specified in the
configuration file for convenience.

Similarly, the implementation is applied to an input text by running:

    python ./synonyms.py apply

In this case, there are four important files: a model file containing
the embedding specified by `--model`, an input text given by
`--input`, an output file `--output`, and a file of requested changes
defined by `--changes`.

The changes file is given in YAML format and defined as a dictionary
assigning positive and negative counts to words. The goal of the
transformation is to bring each count to zero if possible. An example
of a changes file can be found under `test-changes.yml`.

Furthermore, the change of synonyms is controlled by a similarity
threshold. This threshold defines whether two words can be replaced or
not according to the word embedding. It is defined in the
configuration file as `thres`.

## Installation

Following steps are required:

    # create virtualenv or conda environment, e.g.
    conda create --name tpms-synonym python=3.8
    pip install -r requirements
    python
    import nltk
    nltk.download('punkt')
