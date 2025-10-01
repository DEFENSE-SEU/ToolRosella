import os
import sys

# Path settings
source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

from fastmcp import FastMCP
from chemlib.chemistry import calculate_molar_mass, balance_equation
from chemlib.electrochemistry import calculate_cell_potential
from chemlib.thermochemistry import calculate_enthalpy
from chemlib.quantum_mechanics import calculate_energy_levels

# Initialize FastMCP service
mcp = FastMCP("chemistry_service")

@mcp.tool(name="calculate_molar_mass", description="Calculate the molar mass of a chemical compound.")
def calculate_molar_mass_tool(compound: str) -> dict:
    """
    Calculate the molar mass of a given chemical compound.

    Parameters:
        compound (str): The chemical formula of the compound.

    Returns:
        dict: A dictionary containing success, result, or error fields.
    """
    try:
        result = calculate_molar_mass(compound)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="balance_chemical_equation", description="Balance a given chemical equation.")
def balance_chemical_equation_tool(equation: str) -> dict:
    """
    Balance a given chemical equation.

    Parameters:
        equation (str): The unbalanced chemical equation.

    Returns:
        dict: A dictionary containing success, result, or error fields.
    """
    try:
        result = balance_equation(equation)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="calculate_cell_potential", description="Calculate the cell potential of an electrochemical cell.")
def calculate_cell_potential_tool(oxidation_half: str, reduction_half: str) -> dict:
    """
    Calculate the cell potential of an electrochemical cell.

    Parameters:
        oxidation_half (str): The oxidation half-reaction.
        reduction_half (str): The reduction half-reaction.

    Returns:
        dict: A dictionary containing success, result, or error fields.
    """
    try:
        result = calculate_cell_potential(oxidation_half, reduction_half)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="calculate_enthalpy", description="Calculate the enthalpy change of a reaction.")
def calculate_enthalpy_tool(reactants: dict, products: dict) -> dict:
    """
    Calculate the enthalpy change of a reaction.

    Parameters:
        reactants (dict): A dictionary of reactants with their quantities.
        products (dict): A dictionary of products with their quantities.

    Returns:
        dict: A dictionary containing success, result, or error fields.
    """
    try:
        result = calculate_enthalpy(reactants, products)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

@mcp.tool(name="calculate_energy_levels", description="Calculate the energy levels of a quantum system.")
def calculate_energy_levels_tool(principal_quantum_number: int) -> dict:
    """
    Calculate the energy levels of a quantum system.

    Parameters:
        principal_quantum_number (int): The principal quantum number.

    Returns:
        dict: A dictionary containing success, result, or error fields.
    """
    try:
        result = calculate_energy_levels(principal_quantum_number)
        return {"success": True, "result": result, "error": None}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}

def create_app() -> FastMCP:
    """
    Create and return the FastMCP application instance.

    Returns:
        FastMCP: The initialized FastMCP instance.
    """
    return mcp