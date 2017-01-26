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
        shutil.rmtree(folder_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def model_distribution(processes):
    log('modeling distribution...')
    perform_one_pass_variance(os.path.join(sys.argv[1], 'input'), os.path.join(sys.argv[1], 'result1'), processes)
    merge_parallel_data(os.path.join(sys.argv[1], 'result1'), os.path.join(sys.argv[1], 'result2'))
    log('Done.')


def online_variance(enumerated_file_path):
    file_idx, file_path = enumerated_file_path
    mean_var = {}

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
        if mean_var[key]['size'] < 2:
            mean_var[key]['m2'] = None
        else:
            mean_var[key]['m2'] /= float(mean_var[key]['size'])

    log("processed({0})".format(file_idx))
    return file_idx, mean_var


def perform_one_pass_variance(input_folder, result_folder, processes):
    recreate_folder(result_folder)
    listedfiles = get_all_files_in_path(input_folder, 'out')

    p = Pool(processes=processes)
    results = p.map(online_variance, list(enumerate(listedfiles)))

    for r in results:
        file_idx = r[0]
        mean_var = r[1]
        pickle_filepath = os.path.join(result_folder, str(file_idx) + '.pickle')
        with open(pickle_filepath, 'wb+') as f:
            pickle.dump(mean_var, f)


def merge_parallel_data(input_folder, result_folder):
    recreate_folder(result_folder)
    listedfiles = get_all_files_in_path(input_folder, 'pickle')

    merged = {}
    for idx, f in enumerate(listedfiles):
            with open(f, 'rb') as f:
                mean_var = pickle.load(f)
                # print(mean_var)

                for k in sorted(mean_var.keys()):
                    # print(k)
                    if k not in merged:
                        merged[k] = {
                            'count': mean_var[k]['size'],
                            'mean': mean_var[k]['mean'],
                            'm2': mean_var[k]['m2']
                        }
                        continue

                    count_b = mean_var[k]['size']
                    mean_b = mean_var[k]['mean']
                    var_b = mean_var[k]['m2']

                    merged[k]['m2'] = parallel_variance(merged[k]['mean'], merged[k]['count'], merged[k]['m2'], mean_b, count_b, var_b)
                    merged[k]['mean'] = (merged[k]['mean'] * merged[k]['count'] + mean_b * count_b) / float(merged[k]['count'] + count_b)
                    merged[k]['count'] += count_b

    pickle_filepath = os.path.join(result_folder, 'result.pickle')
    with open(pickle_filepath, 'wb+') as f:
        pickle.dump(merged, f)


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

    model_distribution(processes=5)
