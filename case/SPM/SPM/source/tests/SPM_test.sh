#!/bin/bash

test_seq=LQIQLIKLVARKNRKRHPQVQ
#A guessed peptide based on density map of the TOC-TIC supercomplex
test_result=P36495
#Result: Tic214 starting from position 1704


# Test 1
echo "Test 1: $test_seq"
# Running peptidesearch_for_release.py
python scripts/SequencePatternMatching.py -q $test_seq -d tests/uniprot.fasta -o tests/test1.txt
if [ $? -ne 0 ]
then
    echo "Test 1 failed."
    exit 1
fi

if grep -Fq $test_result output/test1_ranked.txt
then
    echo "Test 1 passed."
else
    echo "Test 1 failed."
    exit 1
fi


