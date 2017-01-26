#!/usr/bin/env python

import pickle


def main():
    f1 = './experiments_onepass/result2/result.pickle'
    f2_means = './experiments_twopass/result2/means.pickle'
    f2_stds = './experiments_twopass/result4/stds.pickle'

    p1 = None
    with open(f1, 'rb') as f:
        p1 = pickle.load(f)

    p2m = None
    p2s = None
    with open(f2_means, 'rb') as f:
        p2m = pickle.load(f)

    with open(f2_stds, 'rb') as f:
        p2s = pickle.load(f)

    sum_mean_diff = 0
    sum_var_diff = 0
    for n in p1.keys():
        one_mean = p1[n]['mean']
        one_var = p1[n]['m2']
        two_mean = p2m[n]['mean']
        two_var = p2s[n]['std'] ** 2

        sum_mean_diff += abs(one_mean - two_mean)
        sum_var_diff += abs(one_var - two_var)

    print("mean: {0}".format(sum_mean_diff))
    print("var: {0}".format(sum_var_diff))

if __name__ == "__main__":
    main()
