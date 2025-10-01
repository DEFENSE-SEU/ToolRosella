import os
import sys

# Path settings
source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

# Import statements
try:
    from chemlib.chemistry import Compound, Reaction
    from chemlib.electrochemistry import ElectrochemicalCell
    from chemlib.quantum_mechanics import QuantumMechanics
    from chemlib.thermochemistry import Thermochemistry
    from chemlib.utils import Utils
except ImportError as e:
    raise ImportError("Failed to import required modules from chemlib. Ensure the source directory is correctly set.") from e

# Module description
"""
Adapter class for the MCP plugin, providing a unified interface to interact with the chemlib library.
This adapter handles imports, provides fallback mechanisms, and ensures a consistent return format.
"""

class Adapter:
    """
    Adapter class for the chemlib library.
    Provides methods to interact with various classes and functions in the library.
    """

    def __init__(self):
        """
        Initialize the Adapter class.
        Sets the mode attribute to "import" and prepares the adapter for use.
        """
        self.mode = "import"

    # -------------------------------------------------------------------------
    # Chemistry Module
    # -------------------------------------------------------------------------

    def create_compound(self, formula):
        """
        Create a Compound instance.

        Parameters:
        - formula (str): The chemical formula of the compound.

        Returns:
        - dict: A dictionary containing the status and the created Compound instance or error message.
        """
        try:
            compound = Compound(formula)
            return {"status": "success", "data": compound}
        except Exception as e:
            return {"status": "error", "message": f"Failed to create Compound: {str(e)}"}

    def create_reaction(self, reactants, products):
        """
        Create a Reaction instance.

        Parameters:
        - reactants (dict): A dictionary of reactants with their quantities.
        - products (dict): A dictionary of products with their quantities.

        Returns:
        - dict: A dictionary containing the status and the created Reaction instance or error message.
        """
        try:
            reaction = Reaction(reactants, products)
            return {"status": "success", "data": reaction}
        except Exception as e:
            return {"status": "error", "message": f"Failed to create Reaction: {str(e)}"}

    # -------------------------------------------------------------------------
    # Electrochemistry Module
    # -------------------------------------------------------------------------

    def create_electrochemical_cell(self, anode, cathode):
        """
        Create an ElectrochemicalCell instance.

        Parameters:
        - anode (str): The anode material.
        - cathode (str): The cathode material.

        Returns:
        - dict: A dictionary containing the status and the created ElectrochemicalCell instance or error message.
        """
        try:
            cell = ElectrochemicalCell(anode, cathode)
            return {"status": "success", "data": cell}
        except Exception as e:
            return {"status": "error", "message": f"Failed to create ElectrochemicalCell: {str(e)}"}

    # -------------------------------------------------------------------------
    # Quantum Mechanics Module
    # -------------------------------------------------------------------------

    def create_quantum_mechanics(self, **kwargs):
        """
        Create a QuantumMechanics instance.

        Parameters:
        - kwargs: Additional parameters for QuantumMechanics.

        Returns:
        - dict: A dictionary containing the status and the created QuantumMechanics instance or error message.
        """
        try:
            qm = QuantumMechanics(**kwargs)
            return {"status": "success", "data": qm}
        except Exception as e:
            return {"status": "error", "message": f"Failed to create QuantumMechanics: {str(e)}"}

    # -------------------------------------------------------------------------
    # Thermochemistry Module
    # -------------------------------------------------------------------------

    def create_thermochemistry(self, **kwargs):
        """
        Create a Thermochemistry instance.

        Parameters:
        - kwargs: Additional parameters for Thermochemistry.

        Returns:
        - dict: A dictionary containing the status and the created Thermochemistry instance or error message.
        """
        try:
            thermo = Thermochemistry(**kwargs)
            return {"status": "success", "data": thermo}
        except Exception as e:
            return {"status": "error", "message": f"Failed to create Thermochemistry: {str(e)}"}

    # -------------------------------------------------------------------------
    # Utility Module
    # -------------------------------------------------------------------------

    def call_utils_function(self, function_name, *args, **kwargs):
        """
        Call a utility function from the Utils module.

        Parameters:
        - function_name (str): The name of the utility function to call.
        - args: Positional arguments for the utility function.
        - kwargs: Keyword arguments for the utility function.

        Returns:
        - dict: A dictionary containing the status and the result of the function call or error message.
        """
        try:
            if not hasattr(Utils, function_name):
                raise AttributeError(f"Utils module does not have a function named '{function_name}'")
            func = getattr(Utils, function_name)
            result = func(*args, **kwargs)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": f"Failed to call utility function '{function_name}': {str(e)}"}

    # -------------------------------------------------------------------------
    # Error Handling and Fallback
    # -------------------------------------------------------------------------

    def handle_import_failure(self):
        """
        Handle import failure gracefully.

        Returns:
        - dict: A dictionary containing the status and a fallback message.
        """
        return {
            "status": "error",
            "message": "Failed to import required modules. Ensure the source directory is correctly set and dependencies are installed."
        }