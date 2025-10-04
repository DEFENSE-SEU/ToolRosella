import os
import sys

# Path settings
source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

from fastmcp import FastMCP

# Initialize the MCP service
mcp = FastMCP("sequence_pattern_matching_service")

# Tool: Sequence Pattern Matching
@mcp.tool(name="sequence_pattern_matching", description="Perform sequence pattern matching for target protein alignment")
def sequence_pattern_matching(input_sequence: str, target_sequence: str) -> dict:
    """
    Perform sequence pattern matching for target protein alignment.

    Parameters:
        input_sequence (str): The input sequence to be matched.
        target_sequence (str): The target sequence for alignment.

    Returns:
        dict: A dictionary containing success, result, or error fields.
    """
    try:
        from scripts.SequencePatternMatching import SequencePatternMatching

        # Initialize the sequence pattern matching module
        spm = SequencePatternMatching()

        # Perform the matching operation
        result = spm.match(input_sequence, target_sequence)

        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

# Create the application
def create_app() -> FastMCP:
    """
    Create and return the FastMCP application instance.

    Returns:
        FastMCP: The initialized FastMCP instance.
    """
    return mcp