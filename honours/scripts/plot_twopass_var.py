#!/usr/bin/env python
# python ./plot_twopass_var.py ./vocab.pickle.data experiments_twopass

import sys
import os
import cPickle as pickle
import numpy as np
from matplotlib import pyplot as pl
from scipy.stats.stats import pearsonr

from IPython import embed


def plot_distribution_ranges(means, stds):
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
    x = list(stds.keys())
    y = list([n ** 2 for n in stds.values()])
    pl.plot(x, y, 'ro')

    fig2.show()

    pcoeff_std, pval_std = pearsonr(np.array(x), np.array(y))

    print("Mean:\nPearson correlation coefficient: {0}\nP-value: {1}\n".format(pcoeff_mean, pval_mean))
    print("Std:\nPearson correlation coefficient: {0}\nP-value: {1}\n".format(pcoeff_std, pval_std))

    input()


def get_data(means_filepath, stds_filepath):
    means = None
    stds = None

    with open(means_filepath, 'rb') as mf:
        means = pickle.load(mf)

    with open(stds_filepath, 'rb') as sf:
        stds = pickle.load(sf)

    return means, stds


def main():

    vocab = None
    with open(sys.argv[1], 'rb') as f:
        vocab = pickle.load(f)

    data_means, data_stds = get_data(os.path.join(sys.argv[2], 'result2', 'means.pickle'), os.path.join(sys.argv[2], 'result4', 'stds.pickle'))

    means = {}
    stds = {}
    for key, val in data_means.items():
        freq = vocab[key]['freq']
        means[freq] = val['mean']
        stds[freq] = val['std']

    plot_distribution_ranges(means, stds)


if __name__ == "__main__":
    main()
