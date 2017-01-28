#!/usr/bin/env python2
# python2 plot_histo_parallel.py ./experiments/histo_result2

import sys
import os
import pickle
import glob
import numpy as np
from matplotlib import pyplot as pl
from collections import defaultdict

# from IPython import embed


def get_all_files_in_path(path, extension):
    listedfiles = [f for f in glob.glob(os.path.join(path, '*.' + extension))]
    return listedfiles


def rebin(data, step):
    rebinned = defaultdict(int)
    for k, v in data.items():
        bin = float(k) - (float(k) % step)
        rebinned[bin] = v

    return rebinned


def main():

    colours = ['r', 'g', 'b', 'y']

    fig = pl.figure(1)
    ax = fig.add_subplot(111)
    ax.set_xlabel("Score")
    ax.set_ylabel("Frequency (milions)")
    ax.get_yaxis().get_major_formatter().set_scientific(False)
    # pl.xlim([-20, 10])

    # loop over all result files - each file is one histogram
    listedfiles = get_all_files_in_path(sys.argv[1], 'pickle')
    for idx, file_path in enumerate(listedfiles):
        cl = colours[idx % len(colours)]
        print("{0} - {1}".format(file_path, cl))
        with open(file_path, 'rb') as f:
            histodata = pickle.load(f)
            histodata = rebin(histodata, step=0.2)

            x = [round(x) for x, _ in sorted(histodata.items())]
            y = [y for _, y in sorted(histodata.items())]  # / float(10 ** 6)
            # pl.plot(x, y, color=cl, linewidth=2.0, ls='--')
            pl.bar(x, y, color=cl)
            averaged = np.average(x, weights=y)
            print(averaged)
            print("{0}: {1} with mean: {2} and std: {3}".format(cl, str(len(x)), np.mean(x), np.std(x)))

    fig.show()
    raw_input()


if __name__ == "__main__":
    main()
