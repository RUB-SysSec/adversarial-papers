#!/usr/bin/env python3
# Simple implementation of synonym transformations
# (c) 2021 Konrad Rieck, Erwin Quiring

import argparse
import os
import sys
import yaml
import random
import gensim
import utils

from copy import deepcopy


def parse_args():
    """ Parse arguments """
    parser = argparse.ArgumentParser(description='Synonym transformations')
    parser.add_argument('command', metavar='<cmd>', default='apply',
                        help='command: train, apply')
    parser.add_argument('-r', '--corpus', metavar='<file>',
                        help='set text corpus file for training')
    parser.add_argument('-i', '--input', metavar='<file>',
                        help='set input file for application')
    parser.add_argument('-o', '--output', metavar='<file>',
                        help='set output file for application')
    parser.add_argument('-m', '--model', metavar='<file>',
                        help='set model file for training and application')
    parser.add_argument('-x', '--changes', metavar='<file>',
                        help='set changes file for application')
    parser.add_argument('-c', '--config', metavar='<file>',
                        default="synonyms.yml",
                        help='set configuration file')
    args = parser.parse_args()

    # Load config file and update args
    utils.load_config(args.config, args)

    # Sanity checks
    if args.command == 'train':
        for a in ["corpus"]:
            if not hasattr(args, a):
                utils.error("No %s given for training" % a)
            if not os.path.exists(getattr(args, a)):
                utils.error("%s file '%s' not found" % (
                    a.capitalize(), getattr(args, a))
                            )

    elif args.command == 'apply':
        for a in ["model", "input", "changes"]:
            if not hasattr(args, a):
                utils.error("No %s given for application" % a)
            if not os.path.exists(getattr(args, a)):
                utils.error("%s file '%s' not found" % (
                    a.capitalize(), getattr(args, a))
                            )

    else:
        print("Error: Unknown mode")
        sys.exit(-1)

    return args


def train_word2vec(data, args):
    """ Train word2vec model """
    model = gensim.models.Word2Vec(
        size=args.word2vec_dim, min_count=args.word2vec_min_count,
        workers=os.cpu_count()
    )
    model.build_vocab(data)
    model.train(
        data, total_examples=len(data), epochs=args.word2vec_epochs
    )
    return model


def cmd_train(args):
    """ Command: train """

    # Load and preprocess data
    print(". Loading corpus %s" % args.corpus)
    data = utils.load_data(args.corpus)

    print(". Preprocessing and cleaning corpus of %d bytes" % len(data))
    data = utils.clean_data(data)

    print(". NLTK processing corpus of %d bytes" % len(data))
    data = utils.nltk_process(data, args)

    print(". Extracted %d sentences (stemming: %d, lower: %d)" % (
        len(data), args.nltk_stemming, args.nltk_lower
    ))

    # Train and save word2vec model
    print(". Training word2vec model with %d dimensions and %d epochs" % (
        args.word2vec_dim, args.word2vec_epochs
    ))
    model = train_word2vec(data, args)

    print(". Saving model %s" % args.model)
    model.save(args.model)


def load_changes(args):
    """ Load changes """

    with open(args.changes) as f:
        changes = yaml.load(f, Loader=yaml.FullLoader)

    # Process words similar to original data
    nargs = deepcopy(args)
    nargs.nltk_min_tokens = 0

    nc = {}
    for key in changes:
        clean = utils.nltk_process(key + ".", nargs)
        nc[clean[0][0]] = changes[key]

    return nc


def gen_synonyms(model, changes, threshold):
    """ Generate synonym table """

    # Determine synonyms for requested changes
    syno = {}
    for word in changes:
        try:
            sim = model.wv.most_similar(word)
        except KeyError:
            continue
        sim = list(filter(lambda x: x[1] >= threshold, sim))
        if len(sim) == 0:
            continue

        # Add synonyms from requested words
        if word not in syno:
            syno[word] = []
        syno[word].extend([x[0] for x in sim])

        # Add synomys to requested words
        for wo, _ in sim:
            if wo not in syno:
                syno[wo] = []
            syno[wo].append(word)

    return syno


def apply_word2vec(model, data, changes):
    """ Apply word2vec for rephrasing """

    out = []
    syno = gen_synonyms(model, changes, args.thres)

    for token in data:
        if token not in syno:
            out.append(token)
            continue

        # Choose random synonym
        replace = random.choice(syno[token])

        # Replaced requested word with synonym
        if token in changes and changes[token] < 0:
            out.append(replace)
            changes[token] += 1

        # Add synonym with requested word
        elif replace in changes and changes[replace] > 0:
            out.append(replace)
            changes[replace] -= 1

        else:
            out.append(token)

    return out, changes


def cmd_apply(args):
    """ Command: apply """

    print(". Loading input %s" % args.input)
    data = utils.load_data(args.input)

    print(". NLTK processing input of %d bytes" % len(data))
    data = utils.nltk_process(data, args)
    data = [token for sent in data for token in sent]

    print(". Loading model %s" % args.model)
    model = gensim.models.Word2Vec.load(args.model)

    print(". Loading changes %s" % args.changes)
    changes = load_changes(args)

    print(". Apply model to %d words of text" % len(data))
    data, left = apply_word2vec(model, data, changes)

    print(". Saving output %s" % args.output)
    with open(args.output, "wt") as f:
        f.write(' '.join(data))


if __name__ == "__main__":
    args = parse_args()

    if args.command == "train":
        cmd_train(args)
    elif args.command == "apply":
        cmd_apply(args)

    sys.exit(0)
