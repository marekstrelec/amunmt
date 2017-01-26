#!/usr/bin/env python

import glob
import math
import os
import pickle
import shutil
import sys
from collections import defaultdict
from time import gmtime, strftime


def log(text):
    time = strftime("%H:%M:%S", gmtime())
    print("[{0}] {1}".format(time, text))


def merge_list_of_dicts(list_of_dicts):
    merged_dict = defaultdict(int)
    for d in list_of_dicts:
        for key, val in d.items():
            merged_dict[key] += val

    return merged_dict


def get_all_files_in_path(path, extension):
    listedfiles = [f for f in glob.glob(os.path.join(path, '*.' + extension))]
    return listedfiles


def recreate_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def get_means(input_path, result_folder):
    def compute_mean_one_pass(file_path):
        means_sum = defaultdict(int)
        means_size = defaultdict(int)

        error_a = 0
        error_b = 0
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()

                if not len(line) or line == "$$$$$":
                    continue

                try:
                    wid, score = line.split('\t', 1)
                except ValueError as e:
                    print(line)
                    error_a += 1
                    continue

                try:
                    means_sum[wid] += float(score)
                except ValueError as e:
                    error_b += 1
                    continue

                means_size[wid] += 1

        print('errors {0}-{1}'.format(error_a, error_b))

        return means_sum, means_size

    recreate_folder(result_folder)

    # get all files in the path
    listedfiles = get_all_files_in_path(input_path, 'out')

    # produce a pickle file for each input file containing mean information
    for idx, f in enumerate(listedfiles):
        log("processing [{0}/{1}]".format(idx+1, len(listedfiles)))
        means_sum, means_size = compute_mean_one_pass(f)
        pickle_filepath = os.path.join(result_folder, str(idx)+'.pickle')
        with open(pickle_filepath, 'wb+') as f:
            pickle.dump((means_sum, means_size), f)


def merge_means(input_path, result_folder):
    recreate_folder(result_folder)

    # get all files in the path
    listedfiles = get_all_files_in_path(input_path, 'pickle')

    # load mean information from multiple files
    list_of_mean_sums = []
    list_of_mean_sizes = []
    for n in listedfiles:
        with open(n, 'rb') as f:
            means_sum, means_size = pickle.load(f)
            list_of_mean_sums.append(means_sum)
            list_of_mean_sizes.append(means_size)

    # merge data
    d_sums = merge_list_of_dicts(list_of_mean_sums)
    d_sizes = merge_list_of_dicts(list_of_mean_sizes)

    merged_dict = {}
    for k in d_sums:
        if k not in d_sizes:
            raise Exception('merge_means: Inconsistent data - key {0} not found in d_sizes'.format(k))
        merged_dict[k] = {
            'mean': d_sums[k] / float(d_sizes[k]),
            'size': d_sizes[k]
        }

    # save merged dict
    pickle_filepath = os.path.join(result_folder, 'means.pickle')
    with open(pickle_filepath, 'wb+') as f:
        pickle.dump(merged_dict, f)


def get_stds(input_path, means_file_path, result_folder):
    def compute_stds_one_pass(means, file_path):
        sq_stds_sum = defaultdict(int)

        error_a = 0
        error_b = 0
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()

                if not len(line) or line == "$$$$$":
                    continue

                try:
                    wid, score = line.split('\t', 1)
                except ValueError as e:
                    print(line)
                    error_a += 1
                    continue

                if wid not in means:
                    raise Exception('get_stds: Inconsistent data - wid {0} not found in means'.format(wid))

                try:
                    diff = float(score) - means[wid]['mean']
                    sq_stds_sum[wid] += diff**2
                except ValueError as e:
                    error_b += 1
                    continue

        print('errors {0}-{1}'.format(error_a, error_b))

        return sq_stds_sum

    recreate_folder(result_folder)

    # load means dictionary
    with open(means_file_path, 'rb') as mf:
        means = pickle.load(mf)

        # get all files in the input path
        listedfiles = get_all_files_in_path(input_path, 'out')

        # produce a pickle file for each input file containing mean information
        for idx, f in enumerate(listedfiles):
            log("processing [{0}/{1}]".format(idx+1, len(listedfiles)))
            sq_stds_sum = compute_stds_one_pass(means, f)
            pickle_filepath = os.path.join(result_folder, str(idx)+'.pickle')
            with open(pickle_filepath, 'wb+') as f:
                pickle.dump(sq_stds_sum, f)


def merge_stds(input_path, means_file_path, result_folder):
    recreate_folder(result_folder)

    # get all files in the path
    listedfiles = get_all_files_in_path(input_path, 'pickle')

    # load means dictionary
    with open(means_file_path, 'rb') as mf:
        means = pickle.load(mf)

        # load mean information from multiple files
        list_of_stds_sums = []
        for n in listedfiles:
            with open(n, 'rb') as f:
                sq_stds_sum = pickle.load(f)
                list_of_stds_sums.append(sq_stds_sum)

        # merge data
        d_sums = merge_list_of_dicts(list_of_stds_sums)

        merged_dict = {}
        for k in d_sums:
            if k not in means:
                raise Exception('merge_stds: Inconsistent data - wid {0} not found in means'.format(wid))
            merged_dict[k] = {
                'std': math.sqrt(d_sums[k] / float(means[k]['size']))
            }

        # save merged dict
        pickle_filepath = os.path.join(result_folder, 'stds.pickle')
        with open(pickle_filepath, 'wb+') as f:
            pickle.dump(merged_dict, f)


def show_results(means_filepath, stds_filepath):
    print('----')

    with open(means_filepath, 'rb') as mf:
        means = pickle.load(mf)

        for k in sorted(means.keys()):
            print('mymean {0}: {1}'.format(k, means[k]['mean']))

    print('')
    with open(stds_filepath, 'rb') as sf:
        stds = pickle.load(sf)

        for k in sorted(stds.keys()):
            print('mystd {0}: {1}'.format(k, stds[k]['std']))

    print('----')


def model_distribution():
    if len(sys.argv) < 2:
        raise Exception("Path to input data not specified!")

    log('get_means...')
    get_means(os.path.join(sys.argv[1], 'input'), os.path.join(sys.argv[1], 'result1'))
    log('merge_means...')
    merge_means(os.path.join(sys.argv[1], 'result1'), os.path.join(sys.argv[1], 'result2'))
    log('get_stds...')
    get_stds(os.path.join(sys.argv[1], 'input'), os.path.join(sys.argv[1], 'result2', 'means.pickle'), os.path.join(sys.argv[1], 'result3'))
    log('merge_stds...')
    merge_stds(os.path.join(sys.argv[1], 'result3'), os.path.join(sys.argv[1], 'result2', 'means.pickle'), os.path.join(sys.argv[1], 'result4'))

    log('done.')

if __name__ == "__main__":
    model_distribution()
