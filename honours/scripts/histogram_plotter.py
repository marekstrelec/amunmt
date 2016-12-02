#!/usr/bin/env python

import sys
import math
import numpy as np
from matplotlib import pyplot as pl
from collections import defaultdict, Counter
from IPython import embed


freq = defaultdict(list)


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


def add_histogram(xs, label, bin_factor=2):
    print("{0}: {1} with mean: {2} and std: {3}".format(label, str(len(xs)), np.mean(xs), np.std(xs)))

    from_bin = math.floor(np.min(xs))
    to_bin = math.ceil(np.max(xs))
    n, bins, patches = pl.hist(xs, bins=abs(from_bin - to_bin) * bin_factor, histtype='barstacked', stacked=True, label=label)


def plot_tribin_histogram(freq):
    a = 10
    b = 150
    rare_keys, normal_keys, frequent_keys = split_array(list(freq.values()), a=a, b=b)

    fig = pl.figure()
    ax = fig.add_subplot(111)
    ax.set_title("Score distribution over three frequency buckets")
    ax.set_xlabel("Score")
    ax.set_ylabel("Frequency")

    add_histogram(frequent_keys, "frequent >{0}".format(b))
    add_histogram(normal_keys, "normal {0}-{1}".format(a, b))
    add_histogram(rare_keys, "rare <{0}".format(a))

    pl.legend(loc="upper left")
    pl.show()

    fig.savefig("histogram.png")


def plot_count_histogram(freq, bin_factor=1):
    pl.figure()

    xss = list(sorted([len(freq[k]) for k in freq]))
    cnt = Counter(xss)
    xs = [(k, cnt[k]) for k in cnt]

    pl.plot(xs, 'ro')
    pl.show()


def main():
    if len(sys.argv) < 2:
        raise Exception("Path to histogram data not specified!")

    with open(sys.argv[1], "r") as f:
        for line in f:
            line = line.strip()
            wid, word, cost = line.split('\t', 2)
            freq[wid].append(float(cost))

    # plot_count_histogram(freq)
    plot_tribin_histogram(freq)


if __name__ == "__main__":
    main()
