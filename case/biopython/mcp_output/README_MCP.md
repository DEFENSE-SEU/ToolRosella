# MCP Plugin README

## Overview

The MCP Plugin is a comprehensive tool designed to facilitate bioinformatics analysis using the Biopython library. It provides a wide range of functionalities for sequence input/output operations, interfacing with NCBI's BLAST service, and accessing NCBI's Entrez databases. This plugin is ideal for researchers and developers working in the field of computational biology.

## Installation

To install the MCP Plugin, ensure you have Python installed on your system. You can then install the plugin using pip:

```
pip install biopython
```

Ensure that you have the required dependencies installed:

- Required: `numpy`, `scipy`
- Optional: `matplotlib`, `reportlab`

These dependencies can be installed via pip as well:

```
pip install numpy scipy
pip install matplotlib reportlab
```

## Usage

The MCP Plugin provides several command-line interfaces and modules for various bioinformatics tasks. Below are some of the core functionalities:

### Sequence Input/Output Operations

The `SeqIO` module handles sequence input/output operations. You can parse, read, and write sequence data using this module.

Example usage:

```python
from Bio import SeqIO

# Parsing a FASTA file
for record in SeqIO.parse("example.fasta", "fasta"):
    print(record.id)
    print(record.seq)
```

### BLAST Queries

The `NCBIWWW` module interfaces with NCBI's BLAST service, allowing you to perform BLAST queries directly from your code.

Example usage:

```python
from Bio.Blast import NCBIWWW

result_handle = NCBIWWW.qblast("blastn", "nt", "AGCTGACT")
```

### Entrez Database Access

The `Entrez` module provides access to NCBI's Entrez databases, enabling you to fetch and search for biological data.

Example usage:

```python
from Bio import Entrez

Entrez.email = "your.email@example.com"
handle = Entrez.esearch(db="nucleotide", term="Homo sapiens[orgn]")
record = Entrez.read(handle)
```

## Available Tool Endpoints

- **biopython-blast**: Command-line interface for running BLAST queries.
- **biopython-seqio**: Command-line interface for sequence input/output operations.

## Notes and Troubleshooting

- Ensure that your internet connection is active when using modules that require online access, such as `NCBIWWW` and `Entrez`.
- If you encounter any issues with dependencies, verify that all required and optional packages are installed correctly.
- For detailed documentation and additional examples, visit the [Biopython GitHub repository](https://github.com/biopython/biopython).

## Troubleshooting

- **Import Errors**: Ensure all dependencies are installed. Use `pip list` to verify installed packages.
- **Network Issues**: Check your internet connection if online services are not responding.
- **Email Requirement**: When using the Entrez module, set your email address to comply with NCBI's usage policy.

For further assistance, refer to the Biopython documentation or seek help from the community forums.