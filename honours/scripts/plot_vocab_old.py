#!/usr/bin/env python2
# python2 plot_vocab.py ./normal_vocab.pickle.data ./bpe_vocab.pickle.data ./vocab.pickle.data

import sys
import pickle
import numpy as np
from matplotlib import pyplot as pl


def get_rgb(a, b, c):
    return [a / 255.0, b / 255.0, c / 255.0]


def plot_zipf(nonbpe_freqs, bpe_freqs):
    fig = pl.figure(1)
    ax = fig.add_subplot(111)

    ax.set_xlabel("Rank")
    ax.set_ylabel("Frequency")

    ax.set_yscale("log", nonposy='clip')
    ax.set_xscale("log", nonposx='clip')
    pl.xlim(1.0, 10 ** 6)
    pl.ylim(1.0, 10 ** 8)
    # ax.get_yaxis().get_major_formatter().set_scientific(False)

    # NORMAL
    y = [n[0] for n in nonbpe_freqs]
    x = range(1, len(nonbpe_freqs) + 1)
    colors = get_rgb(102, 194, 165)

    area = 5
    pl.scatter(x, y, s=area, c=colors, alpha=0.9, lw=0, label='normal words')

    # SUB-WORD
    y = [n[0] for n in bpe_freqs]
    x = range(1, len(bpe_freqs) + 1)
    colors = get_rgb(141, 160, 203)
    pl.scatter(x, y, s=area, c=colors, alpha=0.9, lw=0, label='sub-words')
    # pl.plot(x, y, color='g', marker='.', linestyle='None', label='sub-words')
    pl.legend(loc="upper right", numpoints=1)

    pl.savefig('zipf.png')
    fig.show()
    raw_input()


def plot_cumsum(bpe_freqs):
    values = sorted([x[0] / float(10 ** 6) for x in bpe_freqs])
    cumulative = np.cumsum(values)

    fig = pl.figure(1)
    ax = fig.add_subplot(111)
    ax.set_xlabel("Number of words")
    ax.set_ylabel("Accumulated frequency (millions)")
    ax.get_yaxis().get_major_formatter().set_scientific(False)
    ax.grid(True)

    pl.plot(range(len(cumulative)), cumulative, c=get_rgb(141, 160, 203), lw=1.5)
    pl.axvline(x=20000, color=get_rgb(252, 141, 98), ls='--', lw=1.0)
    pl.axvline(x=45000, color=get_rgb(252, 141, 98), ls='--', lw=1.0)

    pl.savefig('cumsum.png')
    fig.show()
    raw_input()


def main():
    nonbpe_freqs = None
    bpe_freqs = None

    def load_data():
        nonbpe_freqs = None
        bpe_freqs = None
        with open(sys.argv[1], 'rb') as f:
            print('loading nonbpe data...')
            nonbpe_vocab = pickle.load(f)
            nonbpe_freqs = list(sorted([(v, k) for k, v in nonbpe_vocab.items()], reverse=True))

        with open(sys.argv[2], 'rb') as f:
            print('loading bpe data...')
            bpe_vocab = pickle.load(f)
            bpe_freqs = list(sorted([(v, k) for k, v in bpe_vocab.items()], reverse=True))
            # bpe_freqs = list(sorted([(v['freq'], k) for k, v in bpe_vocab.items() if v['freq'] > 0], reverse=True))

        return nonbpe_freqs, bpe_freqs

    nonbpe_freqs, bpe_freqs = load_data()

    # check that we have data
    if nonbpe_freqs is None or bpe_freqs is None:
        raise Exception('Something went wrong')

    print('Done.\nplotting...')

    vocab = None
    with open(sys.argv[3], 'rb') as f:
        vocab = pickle.load(f)

    from IPython import embed
    embed()

    sys.exit(0)

    plot_cumsum(bpe_freqs)
    # plot_zipf(nonbpe_freqs, bpe_freqs)


if __name__ == "__main__":
    main()
