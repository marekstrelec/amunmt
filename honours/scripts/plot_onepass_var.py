#!/usr/bin/env python
# python ./plot_onepass_var.py ./bpe_vocab.vocab ./id_to_word_vocab.pickle.vocab experiments/result2/result.pickle

import sys
import pickle
import numpy as np
from matplotlib import pyplot as pl
from scipy.stats.stats import pearsonr

from IPython import embed


def plot_distribution_ranges(means, vars):
    print('Plotting distribution ranges...')
    fig = pl.figure(1)
    ax = fig.add_subplot(111)
    ax.set_title("Mean distribution")
    ax.set_xlabel("Frequency")
    ax.set_ylabel("Mean")
    ax.set_xscale("log", nonposx='clip')
    x = list(means.keys())
    y = list(means.values())
    pl.plot(x, y, 'bo')
    fig.show()

    pcoeff_mean, pval_mean = pearsonr(np.array(x), np.array(y))

    fig2 = pl.figure(2)
    ax2 = fig2.add_subplot(111)
    ax2.set_title("Standard deviation distribution")
    ax2.set_xlabel("Frequency")
    ax2.set_ylabel("Standard deviation")
    ax2.set_xscale("log", nonposx='clip')
    x = list(vars.keys())
    y = list(vars.values())
    pl.plot(x, y, 'ro')

    fig2.show()

    pcoeff_std, pval_std = pearsonr(np.array(x), np.array(y))

    print("Mean:\nPearson correlation coefficient: {0}\nP-value: {1}\n".format(pcoeff_mean, pval_mean))
    print("Std:\nPearson correlation coefficient: {0}\nP-value: {1}\n".format(pcoeff_std, pval_std))

    input()


def main():

    bpe_vocab = None
    with open(sys.argv[1], 'rb') as f:
        bpe_vocab = pickle.load(f)

    id_to_word_vocab = None
    with open(sys.argv[2], 'rb') as f:
        id_to_word_vocab = pickle.load(f)

    data = None
    with open(sys.argv[3], 'rb') as f:
        data = pickle.load(f)

        means = {}
        vars = {}
        for key, val in data.items():
            word = id_to_word_vocab[key]
            freq = bpe_vocab[word]
            means[freq] = val['mean']
            vars[freq] = val['m2']

        plot_distribution_ranges(means, vars)


if __name__ == "__main__":
    main()
