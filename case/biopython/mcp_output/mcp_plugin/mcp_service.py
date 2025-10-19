import os
import sys

source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

from fastmcp import FastMCP
from Bio.SeqIO import parse, read, write
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Blast.NCBIWWW import qblast
from Bio.Entrez import efetch, esearch, email
import Bio.Entrez

# 设置 NCBI Entrez email（必需）
Bio.Entrez.email = "biopython-mcp@huggingface.co"

mcp = FastMCP("biopython_service")

def seqrecord_to_dict(record):
    """Convert a SeqRecord object to a serializable dictionary."""
    return {
        "id": str(record.id),
        "name": str(record.name),
        "description": str(record.description),
        "sequence": str(record.seq),
        "length": len(record.seq),
        "annotations": dict(record.annotations) if record.annotations else {},
        "features": [
            {
                "type": f.type,
                "location": str(f.location),
                "qualifiers": dict(f.qualifiers)
            }
            for f in record.features
        ] if record.features else []
    }

def dict_to_seqrecord(seq_dict):
    """Convert a dictionary back to a SeqRecord object."""
    if isinstance(seq_dict, SeqRecord):
        return seq_dict
    
    # 从字典创建 SeqRecord
    record = SeqRecord(
        Seq(seq_dict.get("sequence", "")),
        id=seq_dict.get("id", ""),
        name=seq_dict.get("name", ""),
        description=seq_dict.get("description", "")
    )
    
    # 添加注释
    if "annotations" in seq_dict:
        record.annotations.update(seq_dict["annotations"])
    
    return record

@mcp.tool(name="seqio_parse", description="Parse sequence data from a file.")
def seqio_parse(file_path: str, format: str) -> dict:
    """
    Parses sequence data from a file.

    Parameters:
    - file_path: Path to the sequence file.
    - format: Format of the sequence file (e.g., 'fasta').

    Returns:
    - A dictionary with success status and parsed sequences or error message.
    """
    try:
        sequences = list(parse(file_path, format))
        # Convert SeqRecord objects to serializable dictionaries
        result = [seqrecord_to_dict(seq) for seq in sequences]
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="seqio_read", description="Read a single sequence from a file.")
def seqio_read(file_path: str, format: str) -> dict:
    """
    Reads a single sequence from a file.

    Parameters:
    - file_path: Path to the sequence file.
    - format: Format of the sequence file (e.g., 'fasta').

    Returns:
    - A dictionary with success status and the sequence or error message.
    """
    try:
        sequence = read(file_path, format)
        # Convert SeqRecord object to serializable dictionary
        result = seqrecord_to_dict(sequence)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="seqio_write", description="Write sequences to a file.")
def seqio_write(sequences, file_path: str, format: str) -> dict:
    """
    Writes sequences to a file.

    Parameters:
    - sequences: List of sequences to write (can be SeqRecord objects or dicts).
    - file_path: Path to the output file.
    - format: Format of the output file (e.g., 'fasta').

    Returns:
    - A dictionary with success status and number of records written or error message.
    """
    try:
        # 如果 sequences 是列表，将每个元素转换为 SeqRecord
        if isinstance(sequences, list):
            records = []
            for seq in sequences:
                if isinstance(seq, dict):
                    records.append(dict_to_seqrecord(seq))
                else:
                    records.append(seq)
        else:
            # 如果是单个对象
            if isinstance(sequences, dict):
                records = [dict_to_seqrecord(sequences)]
            else:
                records = [sequences]
        
        count = write(records, file_path, format)
        return {"success": True, "result": count, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="blast_qblast", description="Run a BLAST query using NCBI's BLAST service.")
def blast_qblast(program: str, database: str, sequence: str) -> dict:
    """
    Runs a BLAST query using NCBI's BLAST service.

    Parameters:
    - program: BLAST program to use (e.g., 'blastn').
    - database: Database to search against (e.g., 'nt').
    - sequence: Sequence to search.

    Returns:
    - A dictionary with success status and BLAST result or error message.
    """
    try:
        result_handle = qblast(program, database, sequence)
        return {"success": True, "result": result_handle.read(), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="entrez_efetch", description="Fetch data from NCBI's Entrez databases.")
def entrez_efetch(db: str, id: str, rettype: str, retmode: str) -> dict:
    """
    Fetches data from NCBI's Entrez databases.

    Parameters:
    - db: Database to fetch from (e.g., 'nucleotide').
    - id: ID of the record to fetch.
    - rettype: Return type (e.g., 'gb').
    - retmode: Return mode (e.g., 'text').

    Returns:
    - A dictionary with success status and fetched data or error message.
    """
    try:
        handle = efetch(db=db, id=id, rettype=rettype, retmode=retmode)
        return {"success": True, "result": handle.read(), "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="entrez_esearch", description="Search NCBI's Entrez databases.")
def entrez_esearch(db: str, term: str) -> dict:
    """
    Searches NCBI's Entrez databases.

    Parameters:
    - db: Database to search (e.g., 'nucleotide', 'protein', 'gene', 'pubmed').
    - term: Search term. Use proper NCBI query syntax:
        - gene_name[GENE] - Search by gene name
        - organism[ORGN] - Search by organism
        - "Homo sapiens"[ORGN] - Species filter
        - "RefSeq"[Filter] - Only RefSeq records

    Returns:
    - A dictionary with success status and search results or error message.
    
    Examples:
    - "TP53[gene] AND human[organism]"
    - "BRCA1[gene]"
    - "insulin[protein name]"
    """
    try:
        # 确保 email 已设置
        if not Bio.Entrez.email:
            Bio.Entrez.email = "biopython-mcp@huggingface.co"
        
        # 使用 retmax 参数获取更多结果
        handle = esearch(db=db, term=term, retmax=100)
        result = handle.read()
        handle.close()
        
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

def create_app() -> FastMCP:
    """
    Creates and returns the FastMCP application instance.

    Returns:
    - FastMCP instance.
    """
    return mcp