#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This python script for Sequence Pattern Matching (SPM) alignment was written by WuLab & YanLab, School of Life Science, Westlake University.
#
# It can help you search target protein sequence with your input peptides sequence from your given sequence database. 
# Input variants are a peptide sequence and a protein sequence database. And output is a ranking protein list, each with a score and matching postion. 
# The most possible searching candidate is at the top of the output files with the lowest score. 
#
# Variant:
# query_seq: String type. It is your given one-letter sequence, which can be as short as 10-20 residues, the longer, the better. The script will search proteins based on it.
# db_fasta: String type. The protein sequence database file's path and name.
# output_dir: String type. It is the output file's path and name.

# All rights reserved. Please cite us if you use it.

import numpy as np
import os
import argparse


volume = {'A':15, 'C':47, 'D':59, 'E':73, 'F':91, 'G':1, 'H':81, 'I':57, 'K':72, 'L':57, 
          'M':75, 'N':58, 'P':41, 'Q':72, 'R':100, 'S':31, 'T':45, 'V':43, 'W':130, 'Y':107, 'X':0}

def volumeScoring(query_seq_volume, uniprot_info, db_seq):
    """
    Arguments:
        - query_seq_volume: list of residue volumes of query sequence.
        - uniprot_info: information read from .fasta database.
        - db_seq: corresponding uniprot sequence.
    """
    query_len = len(query_seq_volume)
    db_seq_volume = np.array([volume[i] for i in db_seq])
    score = 9999
    position = 1
    for i in range(len(db_seq_volume)-query_len):
            s = np.sum(np.abs(db_seq_volume[i:i+query_len]-query_seq_volume))
            score = min(s, score)
            if s <= score:
                position = i+1
    return [uniprot_info, score, position-1]

def loadUniprotDB(db_fasta):
    """
    Argument:
        - db_fasta: directory of .fasta file containing a set of sequences against which you want to query.
    """
    uniprot_info, seq, database = None, None, dict()
    for i in open(db_fasta).readlines():
        if i[0] == '>':
            database[uniprot_info] = seq
            uniprot_info, seq = i.replace(' ', '_').strip(), ''
        else:
            seq += i.split()[0]
    database[uniprot_info] = seq
    database.pop(None)
    return database

def peptideSearching(db_fasta, query_seq, output_file):
    """
    Arguments:
        - db_fasta: directory of .fasta file containing a set of sequences against which you want to query.
        - query_seq: string of protein sequence in one-letter code without gapping, e.g. 'DKLSPIRRAAVVN'.
        - output_file: file of output containing information of scoring and best matching positions, e.g. '/ssd/output.txt'
    """
    database = loadUniprotDB(db_fasta)
    query_seq_volume = np.array([volume[i] for i in query_seq])
    score = [volumeScoring(query_seq_volume, i, j) for i,j in database.items()]
    np.savetxt(output_file, np.array(score), fmt='%s', header='#UniProt_INFO #Score #Position')
    os.system('bash scripts/SPM_ranking.sh %s' % (output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Peptide Searching by WuLab & YanLab in Westlake University")
    parser.add_argument('-q', '--query_seq', type=str, help='Input query sequence in one-letter code without gapping, e.g. DKLSPIRRAAVVN')
    parser.add_argument('-d', '--db_fasta', type=str, help='Input database fasta file, e.g. uniprot.fasta')
    parser.add_argument('-o', '--output_file', type=str, help='Output file path, e.g. output.txt')
    args = parser.parse_args()
    
    
    #query_seq = 'RLMHARFIAWKII'
    query_seq = args.query_seq
    db_fasta = args.db_fasta
    output_file = args.output_file
    
    peptideSearching(db_fasta=db_fasta, query_seq=query_seq, output_file=output_file)
    
