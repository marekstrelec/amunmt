#!/bin/sh

translated_file="../results/translated"

if [ $# -eq 1 ]
  then
    translated_file="$1"
fi

echo "Testing: " "$translated_file"

/Development/Uni/4.year/honours/mosesdecoder/scripts/generic/multi-bleu.perl /Development/Uni/4.year/honours/amunmt/honours/data/ref-cs.txt < "$translated_file"
