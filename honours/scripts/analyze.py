#!/usr/bin/env python

import sys
import os
import math
import numpy as np
import _pickle as cpickle
from matplotlib import pyplot as pl
from collections import defaultdict, Counter

from IPython import embed


def load_full_vocab(filepath):
    if not os.path.isfile(filepath):
        raise Exception("Vocab file not found!")

    full_vocab = dict()
    with open(filepath, "r") as f:
        line_nu = 0
        for line in f:
            line_nu += 1
            line = line.strip()
            if not len(line):
                continue

            wid, word = line.split('\t', 2)
            if wid in full_vocab:
                raise Exception("Vocab file inconsistent!")

            full_vocab[wid] = word

    return full_vocab


def show_unused(freq, full_vocab, used_vocab):
    full_words = set(full_vocab.keys())
    used_words = set(used_vocab.keys())
    unused_words = full_words-used_words

    print("Full-vocab size:\t{0}".format(len(full_words)))
    print("Used-vocab size:\t{0}".format(len(used_words)))
    print("Number of unused: {0}".format(len(unused_words)))

    print("")
    for word in unused_words:
        print("{0}\t{1}".format(word, full_vocab[word]))


def main():
    freq = defaultdict(list)
    used_vocab = dict()
    pickle_file = os.path.basename(sys.argv[2]) + ".pickle"
    if len(sys.argv) < 3:
        raise Exception("Arguments missing: expecting (vocab file, histogram file)")

    if os.path.isfile(pickle_file):
        # load freq from pickle
        print('Loading data from a pickle file...')
        with open(pickle_file, 'rb') as f:
            freq, used_vocab = cpickle.load(f)
    else:
        #embed()
        print('No pickle file found. Bye.')

    full_vocab = load_full_vocab(sys.argv[1])
    show_unused(freq, full_vocab, used_vocab)


if __name__ == "__main__":
    main()
