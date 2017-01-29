#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# python2 plot_histo_parallel.py ./experiments/histo_result2

from __future__ import unicode_literals
import sys
import os
import pickle
import glob
import numpy as np
import math
from matplotlib import pyplot as pl
import matplotlib.mlab as mlab
from collections import defaultdict

from IPython import embed


def get_all_files_in_path(path, extension):
    listedfiles = [f for f in glob.glob(os.path.join(path, '*.' + extension))]
    return listedfiles


def rebin(data, step):
    rebinned = defaultdict(int)
    for k, v in data.items():
        bin2 = float(k) - (float(k) % step)
        rebinned[bin2] += v
    return rebinned


def weighted_avg_and_std(values, weights):
    average = np.average(values, weights=weights)
    variance = np.average((values - average) ** 2, weights=weights)  # Fast and numerically precise
    return (average, math.sqrt(variance))


def plotit(step):

    def get_rgb(a, b, c):
        return [a / 255.0, b / 255.0, c / 255.0]

    colours = [("red", get_rgb(252, 141, 98)), ("green", get_rgb(102, 194, 165)), ("blue", get_rgb(141, 160, 203))]
    alphas = [0.7, 0.8, 0.5, 0.6]
    targets = ['r.pickle', 'n.pickle', 'f.pickle']
    labels = ['rare', 'normal', 'frequent']
    annotations = [(-3.5, 0.17), (-12.5, 0.07), (1, 0.06)]
    # targets = ['r.pickle', 'n.pickle', 'f.pickle', 'z.pickle']
    # targets = [None, None, 'r.pickle']
    # targets = [None, None, None, 'z.pickle']

    fig = pl.figure(1)
    ax = fig.add_subplot(111)
    ax.set_xlabel("Score")
    ax.set_ylabel("Frequency")
    ax.get_yaxis().get_major_formatter().set_scientific(False)
    pl.grid(True)

    for idx, file_name in enumerate(targets):
        if file_name is None:
            continue

        cl = colours[idx % len(colours)]
        al = alphas[idx % len(alphas)]
        label = labels[idx % len(labels)]
        ann = annotations[idx % len(annotations)]
        file_path = os.path.join(sys.argv[1], file_name)

        print("-------\n{0} - {1}".format(file_name, cl[0]))

        with open(file_path, 'rb') as f:
            data = pickle.load(f)
            histodata = rebin(data, step=step)
            print("> " + str(sum([v for v in histodata.values()])))

            x = [round(x, 2) for x, _ in sorted(histodata.items())]
            y = [y / float(10 ** 6) for _, y in sorted(histodata.items())]

            # n, bins, patches = pl.hist(x, weights=y, bins=np.arange(-15, 10, step), alpha=al, color=cl[1], normed=True, label=label)
            # pl.bar(x, y, color=cl, width=step)

            mu, sigma = weighted_avg_and_std(x, y)
            print("mean: {0}; sigma: {1}".format(mu, sigma))

            npdf = mlab.normpdf(np.arange(-15, 10, step), mu, sigma)
            pl.plot(np.arange(-15, 10, step), npdf, color=cl[1], ls='-', linewidth=2, label=label)

            ax.annotate(
                "μ: {0}, σ:{1}".format(round(mu, 1), round(sigma, 1)),
                xy=ann,
                color=cl[1]
            )

    pl.legend(loc="upper right")
    fig.show()
    raw_input()


if __name__ == "__main__":
    plotit(step=0.5)
