#!/usr/bin/env python2
# python2 ./plot_onepass_var.py ./vocab.pickle.data experiments/result3/result.pickle

import sys
import cPickle as pickle
import numpy as np
import matplotlib
matplotlib.use('Agg')

from matplotlib import pyplot as pl
from scipy.stats.stats import pearsonr

from IPython import embed


def plot_distribution_ranges(means, variances):
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
    # fig.show()

    pcoeff_mean, pval_mean = pearsonr(np.array(x), np.array(y))

    fig2 = pl.figure(2)
    ax2 = fig2.add_subplot(111)
    ax2.set_title("Variance distribution")
    ax2.set_xlabel("Frequency")
    ax2.set_ylabel("Variance")
    ax2.set_xscale("log", nonposx='clip')
    x = list(variances.keys())
    y = list(variances.values())
    pl.plot(x, y, 'ro')

    # fig2.show()

    pcoeff_std, pval_std = pearsonr(np.array(x), np.array(y))

    print("Mean:\nPearson correlation coefficient: {0}\nP-value: {1}\n".format(pcoeff_mean, pval_mean))
    print("Std:\nPearson correlation coefficient: {0}\nP-value: {1}\n".format(pcoeff_std, pval_std))

    # raw_input()


def main():

    vocab = None
    with open(sys.argv[1], 'rb') as f:
        vocab = pickle.load(f)

    data = None
    with open(sys.argv[2], 'rb') as f:
        data = pickle.load(f)

        means = {}
        variances = {}
        for key, val in data.items():
            freq = vocab[key]['freq']
            means[freq] = val['mean']
            variances[freq] = val['m2']

        plot_distribution_ranges(means, variances)


if __name__ == "__main__":
    main()
