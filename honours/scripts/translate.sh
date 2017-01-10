#!/bin/sh

set -u
set -e

if [ -z "$HONOURS_DIR" ]; then
	echo "Variable HONOURS_DIR not set!"
	exit 0
fi

BUILD_DIR="$HONOURS_DIR"/amunmt/build
echo $BUILD_DIR

# this sample script translates a test set, including
# preprocessing (tokenization, truecasing, and subword segmentation),
# and postprocessing (merging subword units, detruecasing, detokenization).

# instructions: set paths to mosesdecoder, subword_nmt, and nematus,
# the run "./translate.sh < input_file > output_file"

# suffix of source language
if [ -z "$1" ]; then
	echo "Source language not specified!"
	exit 0
fi

SRC="$1"
echo "SRC=$1"

# suffix of target language
if [ -z "$1" ]; then
        echo "Target language not specified!"
        exit 0
fi

TRG="$2"
echo "TRG=$2"

# path to moses decoder: https://github.com/moses-smt/mosesdecoder
mosesdecoder="$HONOURS_DIR"/mosesdecoder

# path to subword segmentation scripts: https://github.com/rsennrich/subword-nmt

# path to nematus ( https://www.github.com/rsennrich/nematus )

# theano device

# preprocess
$mosesdecoder/scripts/tokenizer/normalize-punctuation.perl -l $SRC | \
$mosesdecoder/scripts/tokenizer/tokenizer.perl -l $SRC -a | \
$mosesdecoder/scripts/recaser/truecase.perl -model $BUILD_DIR/truecase-model.$SRC | \
# translate

$BUILD_DIR/bin/amun -c config-"$1""$2".yml | \

# postprocess
$mosesdecoder/scripts/recaser/detruecase.perl | \
$mosesdecoder/scripts/tokenizer/detokenizer.perl -l $TRG
