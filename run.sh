#!/bin/bash
#
# Use this shell script to compile (if necessary) your code and then execute it. Below is an example of what might be found in this file if your program was written in Python
#
mkdir Tmp/
rm Tmp/*
python ./src/find_political_donors.py ./input/testInput_1000_records.txt ./output/medianvals_by_zip.txt ./output/medianvals_by_date.txt
#python ./src/find_political_donors.py ./input/testInput_small.txt ./output/medianvals_by_zip.txt ./output/medianvals_by_date.txt

