#!/usr/bin/env python2
# python2 plot_vocab.py ./vocab.pickle.data ./nonbpe_vocab.pickle.data

import sys
import pickle
import numpy as np
from matplotlib import pyplot as pl

BREAK_A = 35000
BREAK_B = 70000


def get_rgb(a, b, c):
    return [a / 255.0, b / 255.0, c / 255.0]


def plot_zipf(sorted_vocab, sorted_nonbpe_vocab):
    area = 5
    fig = pl.figure(1)
    ax = fig.add_subplot(111)

    ax.set_xlabel("Rank")
    ax.set_ylabel("Frequency")

    ax.set_yscale("log", nonposy='clip')
    ax.set_xscale("log", nonposx='clip')
    pl.xlim(1.0, 10 ** 7)
    pl.ylim(1.0, 10 ** 8)
    # ax.get_yaxis().get_major_formatter().set_scientific(False)

    # NON-BPE (NORMAL) WORDS
    y = sorted([n[1]['freq'] for n in sorted_nonbpe_vocab], reverse=True)
    x = range(1, len(sorted_nonbpe_vocab) + 1)
    colors = get_rgb(102, 194, 165)

    pl.scatter(x, y, s=area, c=colors, alpha=0.9, lw=0, label='normal words')

    # BPE WORDS
    y = sorted([n[1]['freq'] for n in sorted_vocab], reverse=True)
    x = range(1, len(sorted_vocab) + 1)
    colors = get_rgb(141, 160, 203)
    pl.scatter(x, y, s=area, c=colors, alpha=0.9, lw=0, label='sub-words')
    pl.legend(loc="upper right", numpoints=1)

    pl.savefig('zipf.png')
    fig.show()
    raw_input()


def plot_cumsum(sorted_vocab):
    values = sorted([x[1]['freq'] / float(10 ** 6) for x in sorted_vocab])
    cumulative = np.cumsum(values)

    fig = pl.figure(1)
    ax = fig.add_subplot(111)
    ax.set_xlabel("Number of words")
    ax.set_ylabel("Accumulated frequency (millions)")
    ax.get_yaxis().get_major_formatter().set_scientific(False)
    ax.grid(True)

    pl.plot(range(len(cumulative)), cumulative,
            c=get_rgb(141, 160, 203), lw=1.5)
    pl.axvline(x=BREAK_A, color=get_rgb(252, 141, 98), ls='--', lw=1.0)
    pl.axvline(x=BREAK_B, color=get_rgb(252, 141, 98), ls='--', lw=1.0)

    pl.savefig('cumsum.png')
    fig.show()
    raw_input()


def find_breakpoints(sorted_vocab):
    values = sorted([x[1]['freq'] for x in sorted_vocab])
    print('len of values: {0}'.format(len(values)))
    print("BREAK_A - rank: {0},  freq: {1}".format(BREAK_A, values[BREAK_A]))
    print("BREAK_B - rank: {0},  freq: {1}".format(BREAK_B, values[BREAK_B]))


def main():
    print("Loading BPE data...")
    vocab = None
    with open(sys.argv[1], 'rb') as f:
        vocab = pickle.load(f)
    print('Done.')
    print("Plotting cumsum...")
    sorted_vocab = sorted(vocab.items(), key=lambda x: x[
                          1]['freq'], reverse=False)
    find_breakpoints(sorted_vocab)
    plot_cumsum(sorted_vocab)

    res = raw_input('Continue? [n=exit] ')
    if res.lower() == 'n':
        sys.exit(0)

    print("Loading Non-BPE data... (this may take a while)")
    nonbpe_vocab = None
    with open(sys.argv[2], 'rb') as f:
        nonbpe_vocab = pickle.load(f)
    print('Done.')

    print("Plotting zipf...")
    sorted_nonbpe_vocab = sorted(nonbpe_vocab.items(), key=lambda x: x[
                                 1]['freq'], reverse=False)
    plot_zipf(sorted_vocab, sorted_nonbpe_vocab)
    print('Done.')


if __name__ == "__main__":
    main()
