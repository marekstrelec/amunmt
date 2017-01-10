#!/bin/sh
# $1 = translated file
# $2 = reference file


set -u
set -e

if [ -z "$HONOURS_DIR" ]; then
	echo "Variable HONOURS_DIR not set!"
	exit 0
fi

if [ $# -eq 1 ]
	then
		translated_file="$1"
	else
		translated_file="../results/translated"
fi

echo "Testing: " "$translated_file"
echo "Reference: " "$2"

"$HONOURS_DIR"/mosesdecoder/scripts/generic/multi-bleu.perl "$2" < "$translated_file"
