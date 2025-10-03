import os
import sys

source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

from fastmcp import FastMCP
from tencirchem.static.hamiltonian import get_h_from_hf
from tencirchem.static.uccsd import UCCSD
from pyscf import M
import numpy as np
import scipy.sparse as sp
import scipy.linalg as la

mcp = FastMCP("quantum_chemistry_service")

@mcp.tool(name="create_hamiltonian", description="Create a Hamiltonian for a given molecule.")
def create_hamiltonian(atom_list: list, basis: str) -> dict:
    """
    Create a Hamiltonian for a given molecule.

    Parameters:
        atom_list (list): List of atoms with their coordinates, e.g., [["H", 0, 0, 0], ["H", 0, 0, 0.74]].
        basis (str): Basis set for the calculation, e.g., "sto-3g".

    Returns:
        dict: A dictionary containing success, result (Hamiltonian data), or error.
    """
    try:
        # Create PySCF molecule object
        mol = M(atom=atom_list, basis=basis)
        mol.build()
        # Run RHF calculation
        from pyscf.scf import RHF
        hf = RHF(mol)
        hf.kernel()
        # Create Hamiltonian using the correct API (sparse COO)
        hamiltonian = get_h_from_hf(hf, hcb=False, htype="sparse")
        # serialize COO matrix for transport
        if sp.issparse(hamiltonian):
            h_coo = hamiltonian.tocoo()
            serialized = {
                "format": "coo",
                "shape": h_coo.shape,
                "data": h_coo.data.tolist(),
                "row": h_coo.row.tolist(),
                "col": h_coo.col.tolist(),
            }
            return {"success": True, "result": serialized}
        else:
            # Fallback: try to convert to dense
            arr = np.array(hamiltonian)
            return {"success": True, "result": {"format": "dense", "shape": arr.shape, "data": arr.tolist()}}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="run_ucc", description="Perform UCC calculation for a molecule.")
def run_ucc(atom_list: list, basis: str, ansatz: str) -> dict:
    """
    Perform UCC calculation for a molecule.

    Parameters:
        atom_list (list): List of atoms with their coordinates, e.g., [["H", 0, 0, 0], ["H", 0, 0, 0.74]].
        basis (str): Basis set for the calculation, e.g., "sto-3g".
        ansatz (str): Type of UCC ansatz, e.g., "uccsd".

    Returns:
        dict: A dictionary containing success, result (energy value), or error.
    """
    try:
        # Create PySCF molecule object
        mol = M(atom=atom_list, basis=basis)
        mol.build()
        # Use UCCSD for ansatz
        ucc = UCCSD(mol)
        energy = ucc.kernel()
        return {"success": True, "result": energy}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="simulate_time_evolution", description="Scheme A: evolve from UCCSD ground state under the electronic Hamiltonian.")
def simulate_time_evolution(atom_list: list, basis: str, time: float, steps: int) -> dict:
    """
    Simulate time evolution for a given molecule.

    Parameters:
        atom_list (list): List of atoms with their coordinates, e.g., [["H", 0, 0, 0], ["H", 0, 0, 0.74]].
        basis (str): Basis set for the calculation, e.g., "sto-3g".
        time (float): Total simulation time.
        steps (int): Number of time steps.

    Returns:
        dict: A dictionary containing success, result (time evolution data), or error.
    """
    try:
        # Create PySCF molecule object
        mol = M(atom=atom_list, basis=basis)
        mol.build()
        # Build HF and Hamiltonian (sparse)
        from pyscf.scf import RHF
        hf = RHF(mol)
        hf.kernel()
        h_sparse = get_h_from_hf(hf, hcb=False, htype="sparse")
        h = h_sparse.toarray() if sp.issparse(h_sparse) else np.array(h_sparse)
        # Use UCCSD ground state as initial state
        ucc = UCCSD(mol)
        _ = ucc.kernel()
        psi = np.array(ucc.statevector(), dtype=np.complex128)
        dt = float(time) / max(1, int(steps))
        times = [0.0]
        energies = [float(np.real(np.vdot(psi, h @ psi)))]
        # single-step propagator
        u_dt = la.expm(-1j * h * dt)
        for k in range(int(steps)):
            psi = u_dt @ psi
            t = (k + 1) * dt
            e = float(np.real(np.vdot(psi, h @ psi)))
            times.append(float(t))
            energies.append(e)
        return {"success": True, "result": {"times": times, "energies": energies}}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="get_ucc_parameters", description="Get optimized parameters from a UCC calculation.")
def get_ucc_parameters(atom_list: list, basis: str, ansatz: str) -> dict:
    """
    Get optimized parameters from a UCC calculation.

    Parameters:
        atom_list (list): List of atoms with their coordinates, e.g., [["H", 0, 0, 0], ["H", 0, 0, 0.74]].
        basis (str): Basis set for the calculation, e.g., "sto-3g".
        ansatz (str): Type of UCC ansatz, e.g., "uccsd".

    Returns:
        dict: A dictionary containing success, result (optimized parameters), or error.
    """
    try:
        # Create PySCF molecule object
        mol = M(atom=atom_list, basis=basis)
        mol.build()
        # Use UCCSD for ansatz
        ucc = UCCSD(mol)
        energy = ucc.kernel()
        # Get the optimized parameters
        params = ucc.params
        return {"success": True, "result": {"energy": energy, "parameters": params.tolist()}}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_app():
    """
    Create and return the FastMCP application instance.

    Returns:
        FastMCP: The FastMCP application instance.
    """
    return mcp