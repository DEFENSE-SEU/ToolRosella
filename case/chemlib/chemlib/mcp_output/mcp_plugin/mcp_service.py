import os
import sys
import csv

# Path settings
source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

from fastmcp import FastMCP
# 使用源码中已存在的 API 组合实现 MCP 所需功能
from chemlib.chemistry import calculate_molar_mass, Reaction
from chemlib.electrochemistry import Galvanic_Cell
from chemlib.quantum_mechanics import energy_of_hydrogen_orbital
import chemlib as _chemlib_pkg

# Initialize FastMCP service
mcp = FastMCP("chemistry_service")

# -------------------------------
# 内部辅助：配平方程、原电池电动势、热化学焓查询、量子能级
# -------------------------------

def _balance_equation(equation: str) -> str:
    # 统一箭头为 '>'（chemlib.Reaction.by_formula 使用 '>' 分割）
    normalized = equation.replace("-->", ">").replace("->", ">")
    reaction = Reaction.by_formula(normalized)
    reaction.balance()
    return str(reaction)

def _cell_potential(e1: str, e2: str) -> float:
    # 直接使用 Galvanic_Cell 计算 E0
    cell = Galvanic_Cell(e1, e2)
    return float(cell.E0)

_ENTHALPY_TABLE = None
_ENTHALPY_TABLE_BASE = None  # 无相态键的快速查找

def _normalize_phase_key(key: str) -> str:
    # 允许 "H2O(l)"、"H2O, l"、"H2O ,l"、"H2O" 等形式
    s = key.strip()
    # 替换括号相态为逗号分隔
    s = s.replace(" ", "")
    if "(" in s and ")" in s:
        try:
            base = s[:s.index("(")]
            phase = s[s.index("(") + 1:s.index(")")]
            return f"{base},{phase}"
        except Exception:
            return s
    return s

def _load_enthalpy_table():
    global _ENTHALPY_TABLE, _ENTHALPY_TABLE_BASE
    if _ENTHALPY_TABLE is not None:
        return _ENTHALPY_TABLE

    # 基于已安装（源码路径）包位置定位资源文件
    pkg_dir = os.path.dirname(os.path.abspath(_chemlib_pkg.__file__))
    csv_path = os.path.join(pkg_dir, "resources", "thermochemistry.csv")
    table = {}
    table_base = {}
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                formula = row.get("Formula")
                # 焓列名为 'H'，单位通常 kJ/mol；缺失时跳过
                H_str = row.get("H")
                if not formula or not H_str:
                    continue
                try:
                    value = float(H_str)
                    table.setdefault(formula, value)
                    # 如果是带相态的记录，如 CO2,g，则给无相态键也存一份首选值
                    if "," in formula:
                        base, phase = formula.split(",", 1)
                        # 简单“标准状态”优先级：l > g > s > aq （水优先液态）
                        priority = {"l": 3, "g": 2, "s": 1, "aq": 0}
                        old = table_base.get(base)
                        if old is None or priority.get(phase, -1) > old[0]:
                            table_base[base] = (priority.get(phase, -1), value)
                    else:
                        # 本身无相态的条目
                        table_base.setdefault(formula, (0, value))
                except Exception:
                    continue
    _ENTHALPY_TABLE = table
    _ENTHALPY_TABLE_BASE = {k: v for k, (_, v) in table_base.items()}
    return _ENTHALPY_TABLE

def _calculate_enthalpy(reactants: dict, products: dict) -> float:
    table = _load_enthalpy_table()

    def sum_side(d: dict) -> float:
        total = 0.0
        for formula, coeff in d.items():
            key = _normalize_phase_key(str(formula))
            # 1) 精确匹配（含相态）
            h = table.get(key)
            if h is None:
                # 2) 尝试去掉空白、大小写保持；若 key 中带逗号相态失败，则回退无相态
                if "," in key:
                    base = key.split(",", 1)[0]
                else:
                    base = key
                # 3) 无相态优先使用“标准状态”选择
                h = _ENTHALPY_TABLE_BASE.get(base)
            if h is None:
                h = 0.0
            total += float(coeff) * h
        return total

    # ΔH = ΣνHf(products) − ΣνHf(reactants)
    return sum_side(products) - sum_side(reactants)

def _calculate_energy_levels(n: int) -> float:
    # 直接使用氢原子能级公式（能量，单位 J）
    return float(energy_of_hydrogen_orbital(int(n)))

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
        result = _balance_equation(equation)
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
        # 这里将参数视作两个电极元素符号，例如 "Zn" 与 "Cu"
        result = _cell_potential(oxidation_half, reduction_half)
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
        result = _calculate_enthalpy(reactants, products)
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
        result = _calculate_energy_levels(principal_quantum_number)
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