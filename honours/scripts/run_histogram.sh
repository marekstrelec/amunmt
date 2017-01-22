#!/bin/sh
# $1 = output_file
# $2 = output_histogram_file
# $3 = input_file

# set -u
set -e

# prompts to set all parameters to their default value if not specified
if [ -z "$1" ]; then
        echo "input_file path not specified!"

        input_file="../input/input-cs_one.txt"
        while true; do
        read -p "Do you want to use $input_file ?" yn
        case $yn in
                [Yy]* ) break;;
                [Nn]* ) exit;;
                * ) echo "Please answer Y or N.";;
        esac
        done
else
        input_file="$1"
fi

if [ -z "$2" ]; then
        echo "output_file path not specified!"

	output_file="out/output.out"
	while true; do
    	read -p "Do you want to use $output_file ?" yn
    	case $yn in
        	[Yy]* ) break;;
       		[Nn]* ) exit;;
        	* ) echo "Please answer Y or N.";;
    	esac
	done
else
	output_file="$2"
fi


# remove output files if exist
if [ -f "$output_file" ] ; then
    rm "$output_file"
fi

time make -C ../../build -j
time ./translate.sh cs en < "$input_file" > "$output_file"
cat "$output_file"
