#!/usr/bin/env python2
# python2 parallel_histogram.py ./vocab.pickle.data experiments

import glob
import numpy as np
import os
import cPickle as pickle
import shutil
import sys
from collections import defaultdict
from multiprocessing import Pool
from time import gmtime, strftime


options = ['r', 'n', 'rn', 'f', 'rnf']


def split_vocab(vocab, a, b):
    splitted = dict()
    for o in options:
        splitted[o] = set()

    for k, v in vocab.items():
        if v['freq'] < a:
            splitted['r'].add(k)
            splitted['rn'].add(k)
            splitted['rnf'].add(k)
        elif v['freq'] < b:
            splitted['n'].add(k)
            splitted['rn'].add(k)
            splitted['rnf'].add(k)
        else:
            splitted['f'].add(k)
            splitted['rnf'].add(k)

    return splitted


def log(text):
    time = strftime("%H:%M:%S", gmtime())
    print("[{0}] {1}".format(time, text))


def get_all_files_in_path(path, extension):
    listedfiles = [f for f in glob.glob(os.path.join(path, '*.' + extension))]
    return listedfiles


def recreate_folder(folder_path):
    if os.path.exists(folder_path):
        yes = set(['yes', 'y'])
        no = set(['no', 'n', ''])

        while(True):
            choice = raw_input("A folder exists. Do you want to delete {0}? [y/N] ".format(folder_path)).lower()
            if choice in yes:
                shutil.rmtree(folder_path)
                break
            elif choice in no:
                return False
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        for o in options:
            os.makedirs(os.path.join(folder_path, o))
        return True


def model_histogram(vocab, processes, step):
    log('gathering histodata...')
    perform_parallel_histo(os.path.join(sys.argv[2], 'input'), os.path.join(sys.argv[2], 'histo_result1'), vocab, step, processes)
    log('merging parallel data...')
    for o in options:
        merge_parallel_histodata(os.path.join(sys.argv[2], 'histo_result1', o), os.path.join(sys.argv[2], 'histo_result2'), str(o) + '.pickle')
    log('Done.')


def compute_histodata(params):
    process_idx, chunk, result_folder, vocab, step = params
    histodata = {}
    for o in options:
        histodata[o] = defaultdict(int)

    for idx, file_path in enumerate(chunk):
        try:
            with open(file_path, 'r') as f:
                if idx % 1 == 0:
                    print('processing({0}) ({1}/{2}) - {3}'.format(process_idx, idx + 1, len(chunk), file_path))

                for line in f:
                    line = line.strip()

                    if not len(line) or line == "$$$$$":
                        continue

                    wid, score = line.split('\t', 1)
                    bin = float(score) - (float(score) % step)

                    for o in options:
                        if wid in vocab[o]:
                            histodata[o][bin] += 1

        except EOFError:
            print('>>>>>>> EOFError - file: {0}'.format(file_path))
            continue
        except ValueError:
            print('>>>>>>> ValueError - file: {0}'.format(file_path))
            continue

    for o in options:
        pickle_filepath = os.path.join(result_folder, o, str(process_idx) + '.pickle')
        with open(pickle_filepath, 'wb+') as f:
            pickle.dump(histodata[o], f)


def perform_parallel_histo(input_folder, result_folder, vocab, step, processes):
    def chunkify(lst, n):
        return [lst[i::n] for i in xrange(n)]

    recreated = recreate_folder(result_folder)
    if not recreated:
        return

    listedfiles = get_all_files_in_path(input_folder, 'out')
    chunks = chunkify(listedfiles, processes)

    p = Pool(processes=processes)
    params = [(i, chunks[i], result_folder, vocab, step) for i in xrange(len(chunks))]
    p.map(compute_histodata, params)
    # compute_histodata(params[0])


def merge_parallel_histodata(input_folder, result_folder, result_filename):
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)

    listedfiles = get_all_files_in_path(input_folder, 'pickle')

    merged_histodata = defaultdict(int)
    for file_path in listedfiles:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)

            for key, val in data.items():
                merged_histodata[key] += val

    pickle_filepath = os.path.join(result_folder, result_filename)
    with open(pickle_filepath, 'wb+') as f:
        pickle.dump(merged_histodata, f)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise Exception("Path to input data not specified!")

    vocab = None
    with open(sys.argv[1], 'rb') as f:
        vocab = pickle.load(f)
        splitted_vocab = split_vocab(vocab, 200, 400)

        model_histogram(splitted_vocab, step=0.1, processes=4)
