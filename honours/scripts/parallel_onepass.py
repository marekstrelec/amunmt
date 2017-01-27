#!/usr/bin/env python
# python ./parallel_onepass.py experiments_onepass

import glob
import numpy as np
import os
import pickle
import shutil
import sys
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
        yes = set(['yes', 'y', ''])
        no = set(['no', 'n'])

        while(True):
            choice = raw_input("A folder exists. Do you want to delete {0}? [Y/n] ".format(folder_path)).lower()
            if choice in yes:
                shutil.rmtree(folder_path)
                break
            elif choice in no:
                break
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def model_distribution(processes):
    log('modeling distribution...')
    perform_one_pass_variance(os.path.join(sys.argv[1], 'input'), os.path.join(sys.argv[1], 'result1'), processes)
    log('merging data parallel...')
    merge_data_parallel(os.path.join(sys.argv[1], 'result1'), os.path.join(sys.argv[1], 'result2'), processes)
    log('merging data final...')
    merge_data_final(os.path.join(sys.argv[1], 'result2'), os.path.join(sys.argv[1], 'result3'))
    log('Done.')


def online_variance(params):
    file_idx, file_path, result_folder = params
    mean_var = {}
    pickle_filepath = os.path.join(result_folder, str(file_idx) + '.pickle')

    # skip already generated files
    if os.path.exists(pickle_filepath):
        return

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()

            if not len(line) or line == "$$$$$":
                continue

            wid, score = line.split('\t', 1)
            if wid not in mean_var:
                mean_var[wid] = {
                    'mean': 0.0,
                    'size': 0,
                    'm2': 0.0
                }

            mean_var[wid]['size'] += 1
            delta = float(score) - mean_var[wid]['mean']
            mean_var[wid]['mean'] += delta / float(mean_var[wid]['size'])
            delta2 = float(score) - mean_var[wid]['mean']
            mean_var[wid]['m2'] += delta * delta2

    for key in mean_var:
        if mean_var[key]['size'] > 0:
            mean_var[key]['m2'] /= float(mean_var[key]['size'])

    with open(pickle_filepath, 'wb+') as f:
        pickle.dump(mean_var, f)
    log("processed({0})".format(file_idx))


def perform_one_pass_variance(input_folder, result_folder, processes):
    recreate_folder(result_folder)
    listedfiles = get_all_files_in_path(input_folder, 'out')

    p = Pool(processes=processes)
    params = [(n, listedfiles[n], result_folder) for n in xrange(len(listedfiles))]
    p.map(online_variance, params)


def merge_data(param):
    i, chunk, result_folder = param
    merged = {}
    for idx, f in enumerate(chunk):
        with open(f, 'rb') as f:
            mean_var = pickle.load(f)
            # print(mean_var)

            for k in sorted(mean_var.keys()):
                # print(k)
                if k not in merged:
                    merged[k] = {
                        'size': mean_var[k]['size'],
                        'mean': mean_var[k]['mean'],
                        'm2': mean_var[k]['m2']
                    }
                    continue

                size_b = mean_var[k]['size']
                mean_b = mean_var[k]['mean']
                var_b = mean_var[k]['m2']

                merged[k]['m2'] = parallel_variance(merged[k]['mean'], merged[k]['size'], merged[k]['m2'], mean_b, size_b, var_b)
                merged[k]['mean'] = (merged[k]['mean'] * merged[k]['size'] + mean_b * size_b) / float(merged[k]['size'] + size_b)
                merged[k]['size'] += size_b

        print('merge({0}) ({1}/{2})'.format(i, idx+1, len(chunk)))

    pickle_filepath = os.path.join(result_folder, str(i) + '.pickle')
    with open(pickle_filepath, 'wb+') as f:
        pickle.dump(merged, f)


def merge_data_parallel(input_folder, result_folder, processes):

    def chunkify(lst, n):
        return [lst[i::n] for i in xrange(n)]

    recreate_folder(result_folder)
    listedfiles = get_all_files_in_path(input_folder, 'pickle')
    chunks = chunkify(listedfiles, processes)

    p = Pool(processes=processes)
    params = [(i, chunks[i], result_folder) for i in xrange(len(chunks))]
    p.map(merge_data, params)


def merge_data_final(input_folder, result_folder):
    recreate_folder(result_folder)
    listedfiles = get_all_files_in_path(input_folder, 'pickle')
    print(listedfiles)
    merge_data(('result', listedfiles, result_folder))


def parallel_variance(avg_a, count_a, var_a, avg_b, count_b, var_b):
    combined_avg = (avg_a * count_a + avg_b * count_b) / float(count_a + count_b)
    return (count_a * (var_a + (avg_a - combined_avg) ** 2) + count_b * (var_b + (avg_b - combined_avg) ** 2)) / float(count_a + count_b)


def test():
    model_distribution()

    log('Testing...\n')
    print('My values')
    merged = merge_parallel_data(os.path.join(sys.argv[1], 'result1'))
    for k, v in sorted(merged.items()):
        print('{0}: mean {1}; var {2}'.format(k, v['mean'], v['m2']))

    print('-----')
    print('Real:')
    inp = {
        '1': [3, 5, 7, 7, 3],
        '2': [8, 9, 3, 4, 55],
        '3': [4, 66, 2, 3, 23, 4],
        '4': [1, 3, 16, 17],
        '5': [4, 9, 30, 9, 10, 22]
    }

    for k in sorted(inp.keys()):
        print('{0}: mean {1}; var {2}'.format(k, np.mean(inp[k]), np.std(inp[k]) ** 2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise Exception("Path to input data not specified!")

    model_distribution(processes=12)
