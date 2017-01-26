#!/usr/bin/env python
# python ./plot_histo.py bpe_vocab.pickle id_to_word_vocab.pickle experiments_twopass/input/histogram_in.out

import sys
import math
import numpy as np
import pickle
from matplotlib import pyplot as pl

from IPython import embed


def add_histogram(xs, label, bin_factor=2):
    if len(xs) == 0:
        print("No data points for: \"{0}\" - skipping.".format(label))
        return

    print("{0}: {1} with mean: {2} and std: {3}".format(label, str(len(xs)), np.mean(xs), np.std(xs)))

    from_bin = math.floor(np.min(xs))
    to_bin = math.ceil(np.max(xs))
    n, bins, patches = pl.hist(xs, bins=abs(from_bin - to_bin) * bin_factor, histtype='barstacked', stacked=True, label=label)


def plot_histogram(rare_keys, normal_keys, frequent_keys):
    print('Plotting histogram...')

    fig = pl.figure(1)
    ax = fig.add_subplot(111)
    ax.set_title("Score distribution")
    ax.set_xlabel("Score")
    ax.set_ylabel("Frequency")

    # ax.set_autoscale_on(False)
    # ax.set_xscale("log", nonposx='clip')
    # ax.set_xlim([1, 50])

    add_histogram(frequent_keys, "frequent")
    add_histogram(normal_keys, "normal")
    add_histogram(rare_keys, "rare")

    pl.legend(loc="upper left")
    fig.show()

    input()


def model_histogram():

    bpe_vocab = None
    with open(sys.argv[1], 'rb') as f:
        bpe_vocab = pickle.load(f)

    id_to_word_vocab = None
    with open(sys.argv[2], 'rb') as f:
        id_to_word_vocab = pickle.load(f)

    rare_keys = []
    normal_keys = []
    frequent_keys = []
    num = 0
    with open(sys.argv[3], 'r') as f:
        for line in f:
            num += 1
            if num % 500000 == 0:
                print("{0} processed".format(num))
            # if num>1000000:
            #     break

            line = line.strip()

            if not len(line) or line == "$$$$$":
                continue

            wid, score = line.split('\t', 1)
            word = id_to_word_vocab[wid]
            freq = bpe_vocab[word]

            if int(freq) < 30:
                rare_keys.append(float(score))
            if int(freq) > 500:
                frequent_keys.append(float(score))
            else:
                normal_keys.append(float(score))

    plot_histogram(rare_keys, normal_keys, frequent_keys)



if __name__ == "__main__":
    model_histogram()
