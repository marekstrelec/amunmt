#!/urb/bin/env python2
# python2 ./combine.py ./experiments/input 500

import sys
import os
import glob
from multiprocessing import Pool

PROCESSES = 12

def get_all_files_in_path(path, extension):
    listedfiles = [f for f in glob.glob(os.path.join(path, '*.' + extension))]
    return listedfiles


def chunkify(lst, n):
    return [lst[i::n] for i in xrange(n)]


def combine(params):
    idx, chunk = params
    print("Combining to chunk #{0}".format(idx))
    with open(os.path.join(output_folder, str(idx) + ".out"), "w+") as f1:
        for file_path in chunk:
            with open(file_path, 'r') as f2:
                f1.write(f2.read())


if __name__ == "__main__":
    list_of_files = get_all_files_in_path(sys.argv[1], "out")
    print("> Combining files in {0} from {1} files to {2} files...".format(sys.argv[1], len(list_of_files), sys.argv[2]))

    output_folder = os.path.join(sys.argv[1], "combined")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    else:
        raise Exception("Output folder already exists!")

    chunks = enumerate(chunkify(list_of_files, int(sys.argv[2])))
    p = Pool(processes=PROCESSES)
    p.map(combine, chunks)

    print("Done.")

