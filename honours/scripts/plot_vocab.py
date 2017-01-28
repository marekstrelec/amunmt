#!/usr/bin/env python2
# python2 plot_vocab.py ./nonbpe_vocab.pickle.data ./vocab.pickle.data

import sys
import os
import pickle
import numpy as np
from matplotlib import pyplot as pl


def plot(nonbpe_freqs, bpe_freqs):
    fig = pl.figure(1)
    ax = fig.add_subplot(111)

    ax.set_xlabel("Rank")
    ax.set_ylabel("Frequency")

    ax.set_yscale("log", nonposy='clip')
    ax.set_xscale("log", nonposx='clip')
    pl.xlim(1.0, 10 ** 6)
    pl.ylim(1.0, 10 ** 8)
    # ax.get_yaxis().get_major_formatter().set_scientific(False)

    y = [n[0] for n in nonbpe_freqs]
    x = range(1, len(nonbpe_freqs) + 1)
    colors = [0 / 255.0, 204 / 255.0, 102 / 255.0]

    area = 5
    pl.scatter(x, y, s=area, c=colors, alpha=0.9, lw=0, label='normal words')

    y = [n[0] for n in bpe_freqs]
    x = range(1, len(bpe_freqs) + 1)
    colors = [51 / 255.0, 153 / 255.0, 255 / 255.0]
    pl.scatter(x, y, s=area, c=colors, alpha=0.9, lw=0, label='sub-words')
    # pl.plot(x, y, color='g', marker='.', linestyle='None', label='sub-words')
    pl.legend(loc="upper right", numpoints=1)

    pl.savefig('zipf.png')
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

    # caching
    # cache_path = 'plot_vocab.cache.pickle'
    # if os.path.exists(cache_path):
    #     print('Loading cached file...')
    #     with open(cache_path, 'rb') as f:
    #         nonbpe_freqs, bpe_freqs = pickle.load(f)
    # else:
    #     print('Cached file not found.')
    #     with open(cache_path, 'wb+') as f:
    #         nonbpe_freqs, bpe_freqs = load_data()
    #         print('Saving cache...')
    #         pickle.dump((nonbpe_freqs, bpe_freqs), f)

    nonbpe_freqs, bpe_freqs = load_data()

    # check that we have data
    if nonbpe_freqs is None or bpe_freqs is None:
        raise Exception('Something went wrong')

    print('Done.\nplotting...')
    print(nonbpe_freqs[:10])
    print(bpe_freqs[:10])
    plot(nonbpe_freqs, bpe_freqs)


if __name__ == "__main__":
    main()
