#!/bin/bash

#You can use this script to rank SequencePatternMatching.py results.

if [ $# -ne 1 ]
then
	echo "You should input correct parameters."
	echo "How to use..."
	echo "$0 search_results.txt"
else
	if [ ! -d peptidesearch ]
	then
		mkdir peptidesearch
	fi
	rank_basename=`ls $1 | awk -F '/' '{print $NF}' | awk -F '.txt' '{print $1}'`
	sed -n '2,$p' $1 > peptidesearch/peptidesearch.txt
	awk '{print $2}' peptidesearch/peptidesearch.txt > peptidesearch/peptidesearch_temp1.txt
    awk '{print $1,$3}' peptidesearch/peptidesearch.txt > peptidesearch/peptidesearch_temp2.txt
	if [ ! -d output ]
	then
		mkdir output
	fi
	paste peptidesearch/peptidesearch_temp1.txt peptidesearch/peptidesearch_temp2.txt |sort -n > output/${rank_basename}_ranked.txt
	echo "Done."
	echo "The ranking score is:"
	echo "output/${rank_basename}_ranked.txt"
	rm -r peptidesearch &> /dev/null
fi
