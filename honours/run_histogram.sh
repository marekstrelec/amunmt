#!/bin/sh

set -u
set -e

output_file="output.out"
output_histogram_file="histogram.out"

if [ -f "$output_file" ] ; then
    rm "$output_file"
fi

if [ -f "$output_histogram_file" ] ; then
    rm "$output_histogram_file"
fi


time make -C ../build -j
time ./translate.sh < input-cs_one.txt > "$output_file"
cat "$output_file"
