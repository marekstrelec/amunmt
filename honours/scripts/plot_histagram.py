#!/usr/bin/env python

import sys
import os
import math
import numpy as np
import _pickle as cpickle
from matplotlib import pyplot as pl
from collections import defaultdict, Counter
from IPython import embed
from scipy.stats.stats import pearsonr


def split_array(arr, a=30, b=500):
    print("splitting on: {0} and {1}".format(a, b))
    a_values = []
    b_values = []
    c_values = []
    for v in arr:
        if len(v) <= a:
            a_values.extend(v)
        elif len(v) <= b:
            b_values.extend(v)
        else:
            c_values.extend(v)

    return a_values, b_values, c_values


def get_freq_ranges(freq, step):
    values = defaultdict(list)
    for v in freq:
        d = len(v) // step
        values[d].extend(v)

    return values


def expand_freq(freq):
    all_freq = []
    for fs in list(freq.values()):
        all_freq.extend(fs)

    return all_freq


def add_histogram(xs, label, bin_factor=2):
    if len(xs) == 0:
        print("No data points for: \"{0}\" - skipping.".format(label))
        return

    print("{0}: {1} with mean: {2} and std: {3}".format(label, str(len(xs)), np.mean(xs), np.std(xs)))

    from_bin = math.floor(np.min(xs))
    to_bin = math.ceil(np.max(xs))
    n, bins, patches = pl.hist(xs, bins=abs(from_bin - to_bin) * bin_factor, histtype='barstacked', stacked=True, label=label)


def plot_histogram(freq):
    print('Plotting histogram...')
    a = 60
    b = 600
    rare_keys, normal_keys, frequent_keys = split_array(list(freq.values()), a=a, b=b)

    fig = pl.figure(1)
    ax = fig.add_subplot(111)
    ax.set_title("Score distribution")
    ax.set_xlabel("Score")
    ax.set_ylabel("Frequency")

    # ax.set_autoscale_on(False)
    # ax.set_xscale("log", nonposx='clip')
    ax.set_xlim([1, 50])

    add_histogram(frequent_keys, "frequent >{0}".format(b))
    add_histogram(normal_keys, "normal {0}-{1}".format(a, b))
    add_histogram(rare_keys, "rare <{0}".format(a))

    pl.legend(loc="upper left")
    fig.show()

    # input()
    # fig.savefig("histogram.png")


def plot_distribution_ranges(freq):
    step = 100
    print('Plotting distribution ranges...')
    freq_ranges = get_freq_ranges(list(freq.values()), step)

    means = {}
    stds = {}

    for k in freq_ranges:
        means[k] = np.mean(freq_ranges[k])
        stds[k] = np.std(freq_ranges[k])

    fig = pl.figure(2)
    ax = fig.add_subplot(111)
    ax.set_title("Mean distribution")
    ax.set_xlabel("Frequency (x{0})".format(step))
    ax.set_ylabel("Mean")
    x = list(means.keys())
    y = list(means.values())
    pl.plot(x, y, 'bo')
    fig.show()

    pcoeff_mean, pval_mean = pearsonr(np.array(x), np.array(y))

    fig2 = pl.figure(3)
    ax2 = fig2.add_subplot(111)
    ax2.set_title("Standard deviation distribution")
    ax2.set_xlabel("Frequency (x{0})".format(step))
    ax2.set_ylabel("Standard deviation")
    x = list(stds.keys())
    y = list(stds.values())
    pl.plot(x, y, 'ro')

    fig2.show()

    pcoeff_std, pval_std = pearsonr(np.array(x), np.array(y))

    print("Mean:\nPearson correlation coefficient: {0}\nP-value: {1}\n".format(pcoeff_mean, pval_mean))
    print("Std:\nPearson correlation coefficient: {0}\nP-value: {1}\n".format(pcoeff_std, pval_std))

    # input()
    # embed()


def main():
    freq = defaultdict(list)
    pickle_file = 'histodata.pickle'
    if len(sys.argv) < 2:
        raise Exception("Path to histogram data not specified!")

    if os.path.isfile(pickle_file):
        # load freq from pickle
        print('Loading data from a pickle file...')
        with open(pickle_file, 'rb') as f:
            freq = cpickle.load(f)
    else:
        #embed()
        print('No pickle file found. Loading data...')
        with open(sys.argv[1], "r") as f:
            for line in f:
                line = line.strip()

                if line == "$$$$$":
                    continue

                wid, cost, word = line.split('\t', 2)
                freq[wid].append(float(cost))

        # save freq to pickle
        print('Saving data to a pickle file...')
        with open(pickle_file, 'wb') as f:
            cpickle.dump(freq, f)

    plot_histogram(freq)
    plot_distribution_ranges(freq)

    input()


if __name__ == "__main__":
    main()
