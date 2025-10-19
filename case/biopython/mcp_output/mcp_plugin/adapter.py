import os
import sys

# Path settings
source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

# Import statements
try:
    from Bio.SeqIO import parse, read, write
    from Bio.Blast.NCBIWWW import qblast
    from Bio.Entrez import efetch, esearch
except ImportError as e:
    print("Failed to import required modules. Please ensure all dependencies are installed.")
    raise e

# Adapter class definition
class Adapter:
    """
    Adapter class to interface with the BioPython library functions.
    Provides methods to utilize sequence I/O, BLAST, and Entrez functionalities.
    """
    
    def __init__(self):
        self.mode = "import"
    
    # Sequence I/O Methods
    # -------------------------------------------------------------------------
    
    def seqio_parse(self, file, format):
        """
        Parse a sequence file.
        
        :param file: Path to the sequence file.
        :param format: Format of the sequence file.
        :return: Dictionary with status and parsed sequences.
        """
        try:
            sequences = list(parse(file, format))
            return {"status": "success", "data": sequences}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def seqio_read(self, file, format):
        """
        Read a single sequence from a file.
        
        :param file: Path to the sequence file.
        :param format: Format of the sequence file.
        :return: Dictionary with status and the sequence.
        """
        try:
            sequence = read(file, format)
            return {"status": "success", "data": sequence}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def seqio_write(self, sequences, file, format):
        """
        Write sequences to a file.
        
        :param sequences: List of sequences to write.
        :param file: Path to the output file.
        :param format: Format for the output file.
        :return: Dictionary with status.
        """
        try:
            count = write(sequences, file, format)
            return {"status": "success", "count": count}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # BLAST Methods
    # -------------------------------------------------------------------------
    
    def blast_qblast(self, program, database, sequence):
        """
        Perform a BLAST search using NCBI's BLAST service.
        
        :param program: BLAST program to use (e.g., "blastn").
        :param database: Database to search against (e.g., "nt").
        :param sequence: Sequence to search.
        :return: Dictionary with status and BLAST result.
        """
        try:
            result_handle = qblast(program, database, sequence)
            return {"status": "success", "data": result_handle.read()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Entrez Methods
    # -------------------------------------------------------------------------
    
    def entrez_efetch(self, db, id, rettype, retmode):
        """
        Fetch data from NCBI's Entrez databases.
        
        :param db: Database to fetch from (e.g., "nucleotide").
        :param id: ID of the record to fetch.
        :param rettype: Return type (e.g., "gb").
        :param retmode: Return mode (e.g., "text").
        :return: Dictionary with status and fetched data.
        """
        try:
            handle = efetch(db=db, id=id, rettype=rettype, retmode=retmode)
            return {"status": "success", "data": handle.read()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def entrez_esearch(self, db, term):
        """
        Search NCBI's Entrez databases.
        
        :param db: Database to search (e.g., "nucleotide").
        :param term: Search term.
        :return: Dictionary with status and search results.
        """
        try:
            handle = esearch(db=db, term=term)
            return {"status": "success", "data": handle.read()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Fallback Handling
    # -------------------------------------------------------------------------
    
    def handle_import_failure(self):
        """
        Handle cases where imports fail.
        
        :return: Dictionary with status and message.
        """
        return {"status": "error", "message": "Import failed. Please check your environment and dependencies."}