### SPM
### Introduction
This python script of Sequence Pattern Matching (SPM) alignment was written by WuLab & YanLab, School of Life Sciences, Westlake University.

It can help you search target proteins against a cryo-EM map from a given sequence database. 

Inputs are a query peptide sequence and a protein database for searching. Output is a ranking protein list, each with a score and best matching postion. The most possible candidate is at the top of the output file.

### Usage

# 1. Clone this repository into local

```bash
git clone https://github.com/YanLab-Westlake/SPM.git
```

# 2. Running the test example (optional)
```bash
cd SPM
bash tests/SPM_test.sh
```

# 3. Running the search with your own data
```bash
python scripts/SequencePatternMatching.py -q {One-Letter-Sequence} -d {Search-Sequence-Library} -o {Output_name}
```

### Cite us
If you use this script, please cite the following paper:
Jin et al., Structure of a TOC-TIC supercomplex spanning two chloroplast envelope membranes, Cell (2022), https://doi.org/10.1016/j.cell.2022.10.030

