#!/bin/sh

BUILD_DIR=/home/marekstrelec/codes/amunmt/build

# this sample script translates a test set, including
# preprocessing (tokenization, truecasing, and subword segmentation),
# and postprocessing (merging subword units, detruecasing, detokenization).

# instructions: set paths to mosesdecoder, subword_nmt, and nematus,
# the run "./translate.sh < input_file > output_file"

# suffix of source language
SRC=cs

# suffix of target language
TRG=en

# path to moses decoder: https://github.com/moses-smt/mosesdecoder
mosesdecoder=/home/marekstrelec/codes/mosesdecoder

# path to subword segmentation scripts: https://github.com/rsennrich/subword-nmt

# path to nematus ( https://www.github.com/rsennrich/nematus )

# theano device

# preprocess
$mosesdecoder/scripts/tokenizer/normalize-punctuation.perl -l $SRC | \
$mosesdecoder/scripts/tokenizer/tokenizer.perl -l $SRC -a | \
$mosesdecoder/scripts/recaser/truecase.perl -model $BUILD_DIR/truecase-model.$SRC | \
# translate

$BUILD_DIR/bin/amun -c config.yml

# postprocess
$mosesdecoder/scripts/recaser/detruecase.perl | \
$mosesdecoder/scripts/tokenizer/detokenizer.perl -l $TRG
