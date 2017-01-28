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
        os.makedirs(os.path.join(folder_path, 'r'))
        os.makedirs(os.path.join(folder_path, 'n'))
        os.makedirs(os.path.join(folder_path, 'f'))
        return True


def model_histogram(vocab, processes, step):
    log('gathering histodata...')
    perform_parallel_histo(os.path.join(sys.argv[2], 'input'), os.path.join(sys.argv[2], 'histo_result1'), vocab, step, processes)
    log('merging parallel data...')
    merge_parallel_histodata(os.path.join(sys.argv[2], 'histo_result1', 'r'), os.path.join(sys.argv[2], 'histo_result2'), '0_r.pickle')
    merge_parallel_histodata(os.path.join(sys.argv[2], 'histo_result1', 'n'), os.path.join(sys.argv[2], 'histo_result2'), '1_n.pickle')
    merge_parallel_histodata(os.path.join(sys.argv[2], 'histo_result1', 'f'), os.path.join(sys.argv[2], 'histo_result2'), '2_f.pickle')
    log('Done.')


def compute_histodata(params):
    process_idx, chunk, result_folder, vocab, step = params
    histodata_r = defaultdict(int)
    histodata_n = defaultdict(int)
    histodata_f = defaultdict(int)

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

                    if wid in vocab['r']:
                        histodata_r[bin] += 1
                    if wid in vocab['n']:
                        histodata_n[bin] += 1
                    if wid in vocab['f']:
                        histodata_f[bin] += 1

        except EOFError:
            print('>>>>>>> EOFError - file: {0}'.format(file_path))
            continue
        except ValueError:
            print('>>>>>>> ValueError - file: {0}'.format(file_path))
            continue

    pickle_filepath = os.path.join(result_folder, 'r', str(process_idx) + '.pickle')
    with open(pickle_filepath, 'wb+') as f:
        pickle.dump(histodata_r, f)

    pickle_filepath = os.path.join(result_folder, 'n', str(process_idx) + '.pickle')
    with open(pickle_filepath, 'wb+') as f:
        pickle.dump(histodata_n, f)

    pickle_filepath = os.path.join(result_folder, 'f', str(process_idx) + '.pickle')
    with open(pickle_filepath, 'wb+') as f:
        pickle.dump(histodata_f, f)


def perform_parallel_histo(input_folder, result_folder, vocab, step, processes):
    def chunkify(lst, n):
        return [lst[i::n] for i in xrange(n)]

    recreated = recreate_folder(result_folder)
    if not recreated:
        return

    listedfiles = get_all_files_in_path(input_folder, 'out')[:200]
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
    def split_vocab(vocab, a, b):
        splitted = {
            'r': set(),
            'n': set(),
            'f': set()
        }

        for k, v in vocab.items():
            if v['freq'] < a:
                splitted['r'].add(k)
            elif v['freq'] < b:
                splitted['n'].add(k)
            else:
                splitted['f'].add(k)

        return splitted

    if len(sys.argv) < 3:
        raise Exception("Path to input data not specified!")

    vocab = None
    with open(sys.argv[1], 'rb') as f:
        vocab = pickle.load(f)
        splitted_vocab = split_vocab(vocab, 1000, 50000)

        model_histogram(splitted_vocab, step=0.1, processes=4)
