"""
Streamlit Frontend
"""

import os
import sys
import json
import time
import httpx
import asyncio
import streamlit as st
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import UI components (we'll create simplified versions)
from ui_easytool import UIStyleManager, UIComponentRenderer, ToolCatalogRenderer

# Backend configuration
BACKEND_URL = "http://127.0.0.1:8000"

# Multi-domain tool catalog
TOOL_CATALOG = {
    "Mathematics": [
        {
            "name": "SymPy",
            "description": "Symbolic and numerical mathematics: integrals, Riemann sums, volumes of revolution.",
            "example": "I have a function x**2 * sin(x) * cos(x). Please compute the indefinite integral with respect to the variable x and provide the result in analytical form.",
            "icon": "📐",
        },
    ],
    "Chemistry": [
        {
            "name": "AiZynthFinder",
            "repo": "https://github.com/MolecularAI/aizynthfinder",
            "description": "Retrosynthetic planning - find plausible synthesis routes for organic molecules.",
            "example": "Find synthesis routes for aspirin (C9H8O4).",
            "icon": "🧪",
        },
        {
            "name": "ChemLib",
            "description": "Acid-base equilibrium and basic thermodynamic calculations (pH, reaction enthalpy).",
            "example": "Calculate the pH of a 0.10 M acetic acid solution at 25°C.",
            "icon": "🧪",
        },
    ],
    "Geoscience": [
        {
            "name": "ObsPy",
            "repo": "https://github.com/obspy/obspy",
            "description": "Seismic waveform processing and earthquake analysis.",
            "example": "Perform cross-correlation analysis between two seismic traces and visualize the waveforms.",
            "icon": "🌍",
        },
    ],
    "Bioinformatics": [
        {
            "name": "ESM",
            "description": "Protein sequence analysis and structure prediction (physicochemical properties + 3D structure).",
            "example": "I have a protein sequence: MENFQKVEKIGEGTYGVVYKARNKLTGEVVALKKIRLDTETEGVPSTAIREISLLKELNHPNIVKLLDVIHTENKLYL. Please analyze the basic properties and predicted structure of a given protein sequence.",
            "icon": "🧬",
        },
        {
            "name": "SPM",
            "repo": "https://github.com/YanLab-Westlake/SPM",
            "description": "Volume-based protein sequence pattern matching (e.g., human vs mouse hemoglobin β chains).",
            "example": "Compare human and mouse hemoglobin β-chain sequences. \n>Human_HBB: MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH, \n>Mouse_HBB: MVHLTPEEKSAITALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFG",
            "icon": "🧬",
        },
    ],
    "Agriculture": [
        {
            "name": "Pest Detection",
            "description": "Detect and classify crop pests from field images.",
            "example": "Identify whether there are pests in this crop image and what possible species they are.",
            "icon": "🌾",
        },
    ],
    "Fluid mechanics": [
        {
            "name": "Foam Mesh",
            "description": "Generate refined CFD meshes for incompressible flow over a circular cylinder using gmsh.",
            "example": "I would like to simulate incompressible flow over a circular cylinder. Please use gmsh to generate the\ncomputational mesh: the computational domain extends\nfrom -2.5 to 2.5 in both x and y directions, with mesh\nrefinement around the cylinder",
            "icon": "🌊",
        },
        {
            "name": "Foam Velocity Field",
            "description": "Visualize velocity magnitude and streamlines from CFD simulations around obstacles.",
            "example": "Please visualize the velocity field on the x-y plane,focusing on the magnitude of the velocity U, and generate an intuitive streamline or velocity-magnitude plot.",
            "icon": "🌊",
        },
    ],
}


def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "selected_domain" not in st.session_state:
        st.session_state.selected_domain = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "show_streaming" not in st.session_state:
        st.session_state.show_streaming = False  # Try Example 流式演示
    if "current_tool" not in st.session_state:
        st.session_state.current_tool = None
    if "streaming_stage" not in st.session_state:
        st.session_state.streaming_stage = 0  # 0: thinking, 1: tool call, 2: result
    # 保留字段
    if "pending_streaming" not in st.session_state:
        st.session_state.pending_streaming = False
    # 新增：聊天输入触发的 Agent 演示
    if "show_agent_streaming" not in st.session_state:
        st.session_state.show_agent_streaming = False
    if "force_welcome" not in st.session_state:
        st.session_state.force_welcome = False
    if "streaming_snapshot" not in st.session_state:
        st.session_state.streaming_snapshot = None


def start_new_chat_session():
    """Create a new sidebar chat entry using current messages."""
    new_chat_id = len(st.session_state.chat_history)
    st.session_state.current_chat_id = new_chat_id
    st.session_state.chat_history.append(
        {"id": new_chat_id, "messages": st.session_state.messages.copy()}
    )


def update_current_chat_history():
    """Persist current messages into the selected chat entry."""
    if st.session_state.current_chat_id is None:
        start_new_chat_session()
        return

    for chat_entry in st.session_state.chat_history:
        if chat_entry["id"] == st.session_state.current_chat_id:
            chat_entry["messages"] = st.session_state.messages.copy()
            break


def call_backend(query: str) -> Dict[str, Any]:
    """Call backend API (当前静态演示版本中不再由 chat_input 调用，可保留备用)"""
    try:
        with httpx.Client(timeout=300) as client:
            response = client.post(f"{BACKEND_URL}/run", json={"query": query})
            response.raise_for_status()
            return response.json()
    except Exception as e:  # noqa: BLE001
        return {"success": False, "error": str(e)}


def render_welcome_section() -> bool:
    """Render welcome section with tool catalog

    Returns:
        clicked_example (bool): 是否有 Try Example 被点击
    """
    clicked_example = False

    st.markdown(
        """
    <div style="text-align: center; padding: 1rem 0 2rem 0; margin-top: -1rem;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; margin-bottom: 1.5rem;">
            <div style="font-size: 4rem;">🚀</div>
            <h1 style="font-size: 3.5rem; font-weight: 700;
                       color: #4f9dd8;
                       margin: 0;
                       letter-spacing: -0.02em;">
                SciNexus
            </h1>
        </div>
        <p style="font-size: 2.2rem; color: #1e293b; margin-top: 0; line-height: 1.6;">
            <strong>Find GitHub code, convert to MCP tools, solve your tasks</strong> <span style="color: #64748b;"></span>
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <h3 style="font-size: 2.5rem; font-weight: 700; color: #1e293b; margin-bottom: 1.5rem;">
        🎯 Available Examples
    </h3>
    """,
        unsafe_allow_html=True,
    )

    cols = st.columns(2, gap="large")
    domain_list = list(TOOL_CATALOG.items())

    for idx, (domain, tools) in enumerate(domain_list):
        col = cols[idx % 2]
        with col:
            with st.expander(f"{tools[0]['icon']} {domain}", expanded=False):
                for tool in tools:
                    st.markdown(
                        f"<div style='font-size: 1.35rem; font-weight: 700; margin-bottom: 0.5rem;'>{tool['name']}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div style='font-size: 1.4rem; color: #64748b; margin-bottom: 1rem;'>{tool['description']}</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "▶️ Try Example", key=f"btn_{tool['name']}", use_container_width=True
                    ):
                        example_query = tool.get("example", "")
                        st.session_state.streaming_snapshot = None

                        # 写入新的“用户 query”并开始一个独立的聊天会话
                        st.session_state.messages = [
                            {"role": "user", "content": example_query}
                        ]
                        start_new_chat_session()

                        # 记录当前工具名，供 streaming 使用
                        st.session_state.current_tool = tool["name"]

                        clicked_example = True

                    if tool != tools[-1]:
                        st.markdown("---")

    return clicked_example


def render_processing_status(status_text: str):
    """Render processing status"""
    st.markdown(
        f"""
    <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(16, 185, 129, 0.1));
                border-left: 4px solid #6366f1;
                border-radius: 0.5rem;
                padding: 1rem;
                margin: 1rem 0;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <div style="font-size: 1.5rem;">🔄</div>
            <div style="color: #4f46e5; font-weight: 600;">{status_text}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def get_demo_flow(tool_name: str):
    """获取工具的演示流程：Thinking + Tools + Final Result

    这里是静态演示数据，不实际调用后端。
    """
    demo_flows = {
        # --------------------------------------
        # 1. 数学：符号积分 + 数值积分
        # --------------------------------------
        "SymPy": {
            "thinking": (
                "Step 1: I will first compute the analytical antiderivative of the function "
                "x**2 * sin(x) * cos(x) using a symbolic integration tool.\n\n"
                "Step 2: Then I will show how a Riemann sum can be used to approximate a definite integral "
                "for a related function sin(x**2) on [0, 2].\n\n"
                "Step 3: Finally, I will use a numerical integration-based tool to compute the volume of the "
                "solid obtained by rotating y = sin(x) about the x-axis over [0, π]."
            ),
            "tools": [
                {
                    "name": "indefinite_integral",
                    "params": {
                        "expression": "x**2 * sin(x) * cos(x)",
                        "variable": "x",
                    },
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "result": {\n'
                        '    "integral": "1/8*x^2*sin(2*x) - 1/8*x^2*cos(2*x) '
                        '+ 1/4*x*sin(2*x) - 1/4*sin(2*x) + C",\n'
                        '    "simplified": true\n'
                        "  },\n"
                        '  "error": null\n'
                        "}"
                    ),
                },
                {
                    "name": "riemann_sum",
                    "params": {
                        "expression": "sin(x**2)",
                        "variable": "x",
                        "interval": [0.0, 2.0],
                        "n_subintervals": 1000,
                        "method": "midpoint",
                    },
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "result": {\n'
                        '    "riemann_sum": 0.8047769251073362,\n'
                        '    "method": "midpoint",\n'
                        '    "n_subintervals": 1000\n'
                        "  },\n"
                        '  "error": null\n'
                        "}"
                    ),
                },
                {
                    "name": "calculate_volume",
                    "params": {
                        "expression": "sin(x)",
                        "variable": "x",
                        "interval": [0.0, 3.141592653589793],
                        "n_subintervals": 10000,
                        "method": "disks",
                    },
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "result": {\n'
                        '    "volume": 4.9348022005446595,\n'
                        '    "method": "disks",\n'
                        '    "n_subintervals": 10000\n'
                        "  },\n"
                        '  "error": null\n'
                        "}"
                    ),
                },
            ],
            "result": (
                "✅ Math task Complete!\n\n"
                "1️⃣ Symbolic integral\n"
                "For the function f(x) = x²·sin(x)·cos(x), a valid analytical antiderivative is:\n\n"
                "∫ x²·sin(x)·cos(x) dx = 1/8·x²·sin(2x) - 1/8·x²·cos(2x)\n"
                "                      + 1/4·x·sin(2x) - 1/4·sin(2x) + C.\n\n"
                "2️⃣ Riemann sum approximation\n"
                "Using the midpoint method with 1000 subintervals on [0, 2], the integral\n"
                "∫₀² sin(x²) dx ≈ 0.8047769251.\n\n"
                "3️⃣ Volume of revolution\n"
                "For the solid obtained by rotating y = sin(x) about the x-axis over [0, π], using a disk method with "
                "10,000 segments gives a numerical volume of approximately:\n\n"
                "V ≈ 4.9348022005."
            ),
        },

        # --------------------------------------
        # 2. 化学：pH 计算 + 合成路线
        # --------------------------------------
        "ChemLib": {
            "thinking": (
                "I will treat ChemLib as a chemical reasoning tool to compute weak-acid equilibria. "
                "Here we consider a 0.10 M acetic acid solution (pKa = 4.76) at 25°C and estimate its pH."
            ),
            "tools": [
                {
                    "name": "acid_base_equilibrium",
                    "params": {
                        "acid_name": "acetic acid",
                        "concentration_molar": 0.10,
                        "pKa": 4.76,
                        "temperature_C": 25.0,
                        "ionic_strength": 0.0,
                        "include_activity_correction": True,
                    },
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "result": {\n'
                        '    "H_plus_concentration": 1.34e-3,\n'
                        '    "pH": 2.87,\n'
                        '    "degree_of_dissociation": 0.0134,\n'
                        '    "Ka": 1.74e-5,\n'
                        '    "method": "weak_acid_equilibrium_approximation"\n'
                        "  },\n"
                        '  "error": null\n'
                        "}"
                    ),
                }
            ],
            "result": (
                "✅ pH Calculation Complete!\n\n"
                "System: 0.10 M acetic acid solution at 25°C (pKa = 4.76).\n\n"
                "The equilibrium calculation gives:\n"
                "  • [H⁺] ≈ 1.34 × 10⁻³ M\n"
                "  • pH ≈ 2.87\n"
                "  • Degree of dissociation ≈ 1.34%\n\n"
                "This confirms that acetic acid behaves as a weak acid. Because the solution does not contain a "
                "significant amount of its conjugate base (acetate), it is not an effective buffer system by itself."
            ),
        },
        "AiZynthFinder": {
            "thinking": (
                "I will search for plausible retrosynthetic routes to aspirin (C9H8O4) and rank them by "
                "step count and overall yield."
            ),
            "tools": [
                {
                    "name": "search_retrosynthesis",
                    "params": {"target": "Aspirin (C9H8O4)", "max_depth": 3},
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "routes": 2,\n'
                        '  "best_yield": "95%",\n'
                        '  "top_routes": [\n'
                        '    {"name": "Route 1 - Direct acetylation", "steps": 1, "overall_yield": "95%"},\n'
                        '    {"name": "Route 2 - From phenol", "steps": 3, "overall_yield": "88%"}\n'
                        "  ]\n"
                        "}"
                    ),
                }
            ],
            "result": (
                "✅ Retrosynthetic Analysis Complete!\n\n"
                "Target compound: Aspirin (C₉H₈O₄)\n\n"
                "Top suggested routes:\n\n"
                "【Route 1】Direct acetylation (recommended)\n"
                "  • Salicylic acid + acetic anhydride → aspirin\n"
                "  • Steps: 1\n"
                "  • Overall yield: ~95%\n\n"
                "【Route 2】Starting from phenol\n"
                "  • Phenol → salicylic acid → aspirin\n"
                "  • Steps: 3\n"
                "  • Overall yield: ~88%\n\n"
                "Route 1 is preferred due to its shorter sequence and higher yield, making it more practical "
                "for laboratory-scale synthesis."
            ),
        },

        # --------------------------------------
        # 3. 蛋白质：理化性质 + 结构预测（带图片）+ SPM 序列比对
        # --------------------------------------
        "ESM": {
            "thinking": (
                "Step 1: I will analyze basic physicochemical properties of the given protein sequence, such as "
                "molecular formula, isoelectric point, and hydrophobicity.\n\n"
                "Step 2: Then I will predict its 3D structure and provide a PAE (predicted aligned error) "
                "heatmap to assess the confidence in different regions of the model."
            ),
            "tools": [
                {
                    "name": "analyze_sequence",
                    "params": {
                        "sequence": "MENFQKVEKIGEGTYGVVYKARNKLTGEVVALKKIRLDTETEGVPSTAIREISLLKELNHPNIVKLLDVIHTENKLYL",
                        "analysis_items": [
                            "molecular_formula",
                            "isoelectric_point",
                            "hydrophobicity_profile",
                            "instability_index",
                        ],
                    },
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "result": {\n'
                        '    "molecular_formula": "C1375H2172N368O377S5",\n'
                        '    "atom_count": 4297,\n'
                        '    "isoelectric_point": 9.2,\n'
                        '    "hydrophobicity": "overall_hydrophobic",\n'
                        '    "instability_index": "stable"\n'
                        "  },\n"
                        '  "error": null\n'
                        "}"
                    ),
                },
                {
                    "name": "predict_structure",
                    "params": {
                        "sequence": "MENFQKVEKIGEGTYGVVYKARNKLTGEVVALKKIRLDTETEGVPSTAIREISLLKELNHPNIVKLLDVIHTENKLYL",
                        "output_items": ["pdb_file", "pae_heatmap_image", "plddt_scores"],
                    },
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "result": {\n'
                        '    "pdb_path": "/outputs/protein_model_001.pdb",\n'
                        '    "pae_image_path": "images/protein_structure_pae.png",\n'
                        '    "plddt_mean": 82.3,\n'
                        '    "structural_summary": {\n'
                        '      "secondary_structure": "mixed_alpha_beta",\n'
                        '      "domains": 1,\n'
                        '      "low_confidence_regions": ["10-15", "60-65"]\n'
                        "    }\n"
                        "  },\n"
                        '  "error": null\n'
                        "}"
                    ),
                },
            ],
            "result": (
                "✅ Protein Analysis & Structure Prediction Complete!\n\n"
                "1️⃣ Physicochemical properties\n"
                "  • Approximate molecular formula: C₁₃₇₅H₂₁₇₂N₃₆₈O₃₇₇S₅ (≈ 4,297 atoms)\n"
                "  • Predicted pI ≈ 9.2 → protein is likely positively charged at physiological pH\n"
                "  • Hydrophobicity: overall hydrophobic with a substantial hydrophobic core\n"
                "  • Instability index: classified as stable\n\n"
                "2️⃣ 3D structure and confidence\n"
                "  • Fold type: mixed α/β with one main domain\n"
                "  • Mean pLDDT ≈ 82.3 → overall high confidence\n"
                "  • PAE heatmap shows low error within the core domain and higher error in flexible loops "
                "(e.g., residues 10–15 and 60–65).\n\n"
                "A structure model and PAE heatmap image have been generated (see the visualization panel)."
            ),
        },
        "SPM": {
            "thinking": (
                "I will use the SPM tool to perform volume-based protein sequence pattern matching between the "
                "human and mouse hemoglobin β chains and interpret the homology level."
            ),
            "tools": [
                {
                    "name": "spm_sequence_match",
                    "params": {
                        "query_sequence": "Human_HBB(147 aa)",
                        "target_sequence": "Mouse_HBB(146 aa)",
                        "algorithm": "SPM Volume-based Pattern Matching",
                    },
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "result": {\n'
                        '    "best_score": 14.0,\n'
                        '    "matched_region": "full-length region (~147 aa)",\n'
                        '    "query_length": 147,\n'
                        '    "target_length": 147,\n'
                        '    "volume_difference": 14.0,\n'
                        '    "algorithm": "SPM Volume-based Pattern Matching"\n'
                        "  },\n"
                        '  "error": null\n'
                        "}"
                    ),
                }
            ],
            "result": (
                "✅ SPM Sequence Matching Complete!\n\n"
                "Task: Compare human and mouse hemoglobin β-chain sequences.\n\n"
                "SPM results:\n"
                "  • Best score: 14 (lower = more similar)\n"
                "  • Matched region: essentially full-length β chain (~147 aa)\n"
                "  • Query length: 147 aa\n"
                "  • Target length: 147 aa\n"
                "  • Volume difference: 14 (very small)\n\n"
                "Interpretation:\n"
                "The two β-chain sequences are highly homologous with only minor volumetric differences, indicating "
                "a very high degree of structural and functional similarity between human and mouse hemoglobin β chains."
            ),
        },

        # --------------------------------------
        # 4. 农业
        # --------------------------------------
        "Pest Detection": {
            "thinking": (
                "I will load the trained pest detection model, run inference on the given crop image, "
                "and then interpret the predicted classes and confidences.\n\n"
                "If class ID 0 corresponds to 'no visible pest' or 'background', I will also explain any "
                "secondary predictions with lower confidence that might indicate potential pest species."
            ),
            "tools": [
                {
                    "name": "detect_pest",
                    "params": {
                        "model": {
                            "model": "real_model_loaded",
                            "model_path": "pest/source/src/model/pest/mobile.pt",
                            "is_mock": False,
                        },
                        "image_data": {
                            "image_path": "pest/source/ip102_v1.1/images/00574.jpg",
                            "is_mock": False,
                        },
                    },
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "result": {\n'
                        '    "predictions": [\n'
                        '      {"class_id": 1, "class_name": "rice leaf roller", "confidence": 0.06776047497987747},\n'
                        '      {"class_id": 13, "class_name": "grain spreader thrips", "confidence": 0.06254877895116806},\n'
                        '      {"class_id": 22, "class_name": "red spider", "confidence": 0.004129475448280573},\n'
                        '      {"class_id": 45, "class_name": "alfalfa weevil", "confidence": 0.002610716735944152}\n'
                        "    ],\n"
                        '    "top_prediction": {"class_id": 0, "confidence": 0.8540160059928894},\n'
                        '    "is_mock": false\n'
                        "  },\n"
                        '  "error": null\n'
                        "}"
                    ),
                }
            ],
            "result": (
                "✅ Pest Detection Complete!\n\n"
                "Input: field image of crop leaves.\n\n"
                "Model output:\n"
                "  • Top prediction: class ID 0 (internal 'no visible pest / background' label),\n"
                "    confidence ≈ 85.4%.\n\n"
                "  • Additional pest candidates from the model's custom label mapping:\n"
                "      - Class ID 1  (\"rice leaf roller\")        — confidence ≈ 6.8%\n"
                "      - Class ID 13 (\"grain spreader thrips\")   — confidence ≈ 6.3%\n"
                "      - Class ID 22 (\"red spider\")              — confidence ≈ 0.4%\n"
                "      - Class ID 45 (\"alfalfa weevil\")          — confidence ≈ 0.3%\n\n"
                "Interpretation:\n"
                "The detector assigns its highest probability to the background / no-visible-pest class (ID 0),\n"
                "while named pest species only appear with much lower confidence scores.\n\n"
                "From a practical perspective, this image would be classified as having **no clear pest "
                "infestation**. The low-probability pest candidates can be treated as weak hints rather than\n"
                "strong evidence. In a real workflow, an agronomist or plant protection expert might still\n"
                "inspect the leaves manually if early-stage symptoms are a concern."
            ),
        },

        # --------------------------------------
        # 5. CFD：Foam 网格 + 速度场可视化（带图片）
        # --------------------------------------
        "Foam Mesh": {
            "thinking": (
                "I will use a mesh-generation tool (backed by gmsh) to create a 2D unstructured triangular mesh "
                "for incompressible flow over a circular cylinder, with refinement near the cylinder and in the wake."
            ),
            "tools": [
                {
                    "name": "generate_mesh",
                    "params": {
                        "geometry": "cylinder_2d",
                        "domain": {
                            "x_min": -2.5,
                            "x_max": 2.5,
                            "y_min": -2.5,
                            "y_max": 2.5,
                        },
                        "cylinder": {"center": [0.0, 0.0], "radius": 0.5},
                        "mesh_options": {
                            "type": "triangular_unstructured",
                            "refinement_regions": [
                                {"region": "near_cylinder", "cell_size": 0.01},
                                {"region": "wake_region", "cell_size": 0.02},
                            ],
                            "background_cell_size": 0.05,
                        },
                        "export_format": "msh",
                    },
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "result": {\n'
                        '    "mesh_path": "meshes/cylinder_flow_2d.msh",\n'
                        '    "n_nodes": 84231,\n'
                        '    "n_elements": 167904,\n'
                        '    "mesh_type": "triangular_unstructured",\n'
                        '    "quality_stats": {\n'
                        '      "min_quality": 0.32,\n'
                        '      "mean_quality": 0.84\n'
                        "    }\n"
                        "  },\n"
                        '  "error": null\n'
                        "}"
                    ),
                }
            ],
            "result": (
                "✅ CFD Mesh Generation Complete!\n\n"
                "Domain: [-2.5, 2.5] × [-2.5, 2.5], circular cylinder of radius 0.5 at the center.\n\n"
                "Mesh summary:\n"
                "  • Type: 2D unstructured triangular mesh\n"
                "  • Nodes: ≈ 84k\n"
                "  • Elements: ≈ 168k\n"
                "  • Strong refinement near the cylinder surface and in the downstream wake region\n"
                "  • Mesh quality: mean element quality ≈ 0.84 (suitable for incompressible flow simulation)\n\n"
                "This mesh can be directly used in a CFD solver (e.g., OpenFOAM) to simulate incompressible flow "
                "around the cylinder and resolve boundary layers and wake structures."
            ),
        },
        "Foam Velocity Field": {
            "thinking": (
                "I will read the CFD solution for the cylinder flow case and generate visualizations of the velocity "
                "magnitude |U| and streamlines on the x-y plane."
            ),
            "tools": [
                {
                    "name": "visualize_velocity",
                    "params": {
                        "case_directory": "cases/cylinder_flow",
                        "field_name": "U",
                        "plane": "xy",
                        "output_items": [
                            "streamline_plot",
                            "velocity_magnitude_contours",
                        ],
                    },
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "result": {\n'
                        '    "streamline_image_path": "images/cfd_velocity_field.png",\n'
                        '    "magnitude_contour_image_path": "images/cfd_velocity_field.png",\n'
                        '    "U_min": 0.0,\n'
                        '    "U_max": 1.8\n'
                        "  },\n"
                        '  "error": null\n'
                        "}"
                    ),
                }
            ],
            "result": (
                "✅ CFD Velocity Visualization Complete!\n\n"
                "The generated plots show:\n\n"
                "  • Streamlines bending smoothly around the cylinder, with a stagnation point at the front and a "
                "well-defined wake behind the cylinder.\n"
                "  • Velocity magnitude |U| represented by color (blue → red). Low velocities are found near the "
                "stagnation region in front of the cylinder and in the wake, while higher velocities occur along "
                "the sides where the flow accelerates around the obstacle.\n\n"
                "A velocity field visualization image has been generated."
            ),
        },

        # --------------------------------------
        # 6. 地球科学：ObsPy（保留，但稍微润色文案）
        # --------------------------------------
        "ObsPy": {
            "thinking": (
                "I will process seismic waveform data using ObsPy, estimate basic source parameters "
                "such as magnitude and depth, and then visualize the waveforms and cross-correlation results."
            ),
            "tools": [
                {
                    "name": "analyze_seismic",
                    "params": {
                        "waves": ["P", "S"],
                        "method": "time_difference",
                        "stations": 5,
                    },
                    "result": (
                        "{\n"
                        '  "success": true,\n'
                        '  "magnitude": 6.0,\n'
                        '  "depth_km": 15.3,\n'
                        '  "distance_km": 52.0,\n'
                        '  "latitude_deg": 35.23,\n'
                        '  "longitude_deg": 139.76,\n'
                        '  "p_arrival_s": 2.8,\n'
                        '  "s_arrival_s": 4.9,\n'
                        '  "wave_amplitude_cm": 2.3,\n'
                        '  "dominant_frequency_hz": 1.5,\n'
                        '  "waveform_image_path": "images/cross_correlation_analysis.png"\n'
                        "}"
                    ),
                }
            ],
            "result": (
                "✅ Seismic Analysis Complete!\n\n"
                "Epicenter parameters:\n"
                "  • Magnitude: 6.0 (Richter scale)\n"
                "  • Depth: 15.3 km\n"
                "  • Epicentral distance: 52 km\n"
                "  • Location: 35.23°N, 139.76°E\n\n"
                "Seismic wave characteristics:\n"
                "  • P-wave arrival: 2.8 s\n"
                "  • S-wave arrival: 4.9 s\n"
                "  • Peak amplitude: 2.3 cm\n"
                "  • Dominant frequency: 1.5 Hz\n\n"
                "A waveform and cross-correlation visualization has been generated."
            ),
        },
    }

    return demo_flows.get(
        tool_name,
        {
            "thinking": "Processing...",
            "tools": [],
            "result": "Done!",
        },
    )


def render_streaming_response():
    """渲染流式响应（包括查询、思考过程、工具调用和最终结果）
    —— 用于上方 Try Example 区域
    """
    import json as _json

    # 获取当前工具和演示流程
    tool_name = st.session_state.current_tool
    flow = get_demo_flow(tool_name)

    # 从session state获取用户查询
    user_query = ""
    for message in st.session_state.messages:
        if message.get("role") == "user":
            user_query = message.get("content", "")
            break

    st.markdown(
        "<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True
    )

    # 0. 显示用户查询（在最上面，逐字显示）
    time.sleep(1)
    st.markdown("#### 👤 User Query")
    query_container = st.empty()
    query_text = ""
    for char in user_query:
        query_text += char
        query_container.markdown(f"> {query_text}")
        time.sleep(0.02)

    # 在用户查询下面显示害虫图片（仅 Pest Detection 案例）
    if st.session_state.current_tool == "Pest Detection":
        st.image(
            "images/pest.png",  
            # caption="Input crop image for pest detection",
            width=320,
        )
    
    st.markdown("---")

    # 1. 思考过程
    time.sleep(1.5)
    st.markdown("#### 🧠 Thinking Process")
    thinking_container = st.empty()
    thinking_text = ""
    for char in flow["thinking"]:
        thinking_text += char
        thinking_container.markdown(f"```\n{thinking_text}\n```")
        time.sleep(0.05)

    st.markdown("---")

    # 2. 工具调用 - 统一在一个框里输出
    time.sleep(1.5)
    st.markdown("#### 🔧 Tool Calls")
    tool_container = st.empty()
    full_tool_text = ""

    # 先生成完整的工具调用文本
    tool_lines = []
    for tool_call in flow["tools"]:
        tool_name_str = tool_call["name"]
        params = tool_call["params"]
        result = tool_call["result"]

        tool_lines.append(f"✓ Called {tool_name_str}")
        tool_lines.append("Parameters:")
        params_str = _json.dumps(params, indent=2, ensure_ascii=False)
        tool_lines.append(params_str)
        tool_lines.append("Result:")
        tool_lines.append(result)
        tool_lines.append("")

    full_tool_content = "\n".join(tool_lines)

    # 逐字符显示工具调用在同一个框里
    for char in full_tool_content:
        full_tool_text += char
        tool_container.code(full_tool_text, language="")
        time.sleep(0.02)

    st.markdown("---")

    # 3. 最终结果
    time.sleep(1.5)
    st.markdown("#### ✨ Final Result")
    result_container = st.empty()
    result_text = ""
    for char in flow["result"]:
        result_text += char
        quoted = "> " + result_text.replace("\n", "\n> ")
        result_container.markdown(quoted)
        time.sleep(0.05)

    # 如果是带图片的案例，单独展示图像
    current_tool = st.session_state.current_tool
    if current_tool == "ObsPy":
        st.image(
            "images/cross_correlation_analysis.png",
            # caption="Cross-correlation waveform analysis",
            width=640,
        )
    elif current_tool == "Foam Velocity Field":
        st.image(
            "images/cfd_velocity_field.png",
            # caption="CFD velocity magnitude and streamlines",
            width=210,
        )
    elif current_tool == "ESM":
        st.image(
            "images/protein_structure_pae.png",
            # caption="Predicted protein structure and PAE heatmap",
            width=480,
        )

    # 将静态演示的结果同步到聊天记录
    tool_markdown = (
        f"```\n{full_tool_content}\n```"
        if full_tool_content.strip()
        else "_No tool calls executed._"
    )
    assistant_summary = "\n\n".join(
        [
            "#### 🧠 Thinking Process",
            flow["thinking"],
            "#### 🔧 Tool Calls",
            tool_markdown,
            "#### ✨ Final Result",
            flow["result"],
        ]
    )
    
    if current_tool == "ObsPy":
        assistant_summary += (
        "\n\n![Cross-correlation waveform analysis]"
        "(images/cross_correlation_analysis.png)"
    )
    elif current_tool == "Foam Velocity Field":
        assistant_summary += (
            "\n\n![CFD velocity magnitude and streamlines]"
            "(images/cfd_velocity_field.png)"
        )
    elif current_tool == "ESM":
        assistant_summary += (
            "\n\n![Predicted protein structure and PAE heatmap]"
            "(images/protein_structure_pae.png)"
        )
    elif current_tool == "Foam Mesh":
        assistant_summary += (
            "\n\n![CFD mesh around a circular cylinder (gmsh)]"
            "(images/mesh.png)"
        )


    st.session_state.messages.append({"role": "assistant", "content": assistant_summary})
    update_current_chat_history()
    st.session_state.streaming_snapshot = {
        "user_query": user_query,
        "thinking": flow["thinking"],
        "tool_content": full_tool_content,
        "result": flow["result"],
        "tool_name": st.session_state.current_tool,
    }
    st.session_state.show_streaming = False
    st.session_state.force_welcome = False
    st.rerun()


def render_streaming_snapshot(snapshot: Dict[str, Any]):
    """渲染动画结束后的静态快照，保持同样的布局"""
    st.markdown(
        "<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True
    )
    st.markdown("#### 👤 User Query")
    st.markdown(f"> {snapshot.get('user_query', '')}")
    st.markdown("---")

    st.markdown("#### 🧠 Thinking Process")
    st.markdown(f"```\n{snapshot.get('thinking', '')}\n```")
    st.markdown("---")

    st.markdown("#### 🔧 Tool Calls")
    tool_content = snapshot.get("tool_content", "")
    if tool_content.strip():
        st.code(tool_content, language="")
    else:
        st.markdown("_No tool calls executed._")
    st.markdown("---")

    st.markdown("#### ✨ Final Result")
    result_lines = snapshot.get("result", "")
    quoted = "> " + result_lines.replace("\n", "\n> ")
    st.markdown(quoted)

    tool_name = snapshot.get("tool_name")
    if tool_name == "ObsPy":
        st.image(
            "images/cross_correlation_analysis.png",
            # caption="Cross-correlation waveform analysis",
            width=640,
        )
    elif tool_name == "Foam Velocity Field":
        st.image(
            "images/cfd_velocity_field.png",
            # caption="CFD velocity magnitude and streamlines",
            width=210,
        )
    elif tool_name == "ESM":
        st.image(
            "images/protein_structure_pae.png",
            # caption="Predicted protein structure and PAE heatmap",
            width=480,
        )
    elif tool_name == "Foam Mesh":
        st.image(
            "images/mesh.png",
            # caption="CFD mesh around a circular cylinder (gmsh)",
            width=400,
        )


def render_agent_streaming_response():
    """底部聊天输入触发的静态 Agent 演示：
    Query -> 生成 Topics -> GitHub 搜索 & Judgement -> MCP 部署 -> Tool 调用 -> 最终结果
    """
    import json as _json

    # 固定展示的 Query
    fixed_query = "Given the equation x^2 + 5x + 6 = 0, please solve for x."

    st.markdown(
        "<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True
    )

    # 0. 显示用户 Query
    time.sleep(0.8)
    # st.markdown("### 🔍 SciNexus")
    st.markdown("#### 👤 User Query")
    query_container = st.empty()
    q_text = ""
    for ch in fixed_query:
        q_text += ch
        query_container.markdown(f"> {q_text}")
        time.sleep(0.04)
    st.markdown("---")

    # 1. Topic → GitHub 搜索 → 判断 → 找到 sympy
    time.sleep(1.0)
    st.markdown("#### 🧠 GitHub Repository Search")
    topics_container = st.empty()

    full_block = ""
    steps = [
        "Step 1: Generate topics from the query...",
        "Topics: quadratic-equations, algebra, math-solver",
        "",
        "Step 2: Search GitHub repositories using these topics and keywords...",
        "Found candidate repository: sympy",
        "",
        "LLM judgement for sympy:",
        "Reason: SymPy is a Python-based symbolic mathematics library providing features such as equation solving, "
        "calculus, algebraic manipulation, and more. It includes `solve()` for solving polynomial equations directly, "
        "which perfectly matches the requirement to solve x^2 + 5x + 6 = 0.",
        "Judge: Yes ✅",
        "",
        "Selected repository: SymPy -> https://github.com/sympy/sympy",
    ]
    text_all = "\n".join(steps)
    for ch in text_all:
        full_block += ch
        topics_container.markdown(f"```text\n{full_block}\n```")
        time.sleep(0.015)

    st.markdown("---")

    # 2. MCP 服务部署静态演示（SymPy）
    time.sleep(1.0)
    st.markdown("#### 🚀 Deploy MCP")
    deploy_container = st.empty()

    deploy_steps = [
        "Initializing MCP server for repository 'sympy'...",
        "Cloning repository: https://github.com/sympy/sympy",
        "Setting up Python environment and installing SymPy...",
        "Registering MCP tool: sympy_solve(a, b, c)...",
        "Starting MCP process and running import tests...",
        "MCP deployment completed successfully. ✅",
    ]

    deployed_lines = []
    for line in deploy_steps:
        deployed_lines.append(line)
        deploy_container.markdown(
            "```text\n" + "\n".join(deployed_lines) + "\n```"
        )
        time.sleep(1.0)

    st.markdown("---")

    # 3. 调用 sympy.solve()
    time.sleep(1.0)
    st.markdown("#### 🔧 Tool Call")
    tool_container = st.empty()

    params = {"a": 1, "b": 5, "c": 6}
    result_obj = {
        "success": True,
        "roots": [-2, -3],
        "method": "sympy.solve",
    }

    tool_lines = []
    tool_lines.append("✓ Called tool: sympy_solve")
    tool_lines.append("Parameters:")
    tool_lines.append(_json.dumps(params, indent=2))
    tool_lines.append("")
    tool_lines.append("Result:")
    tool_lines.append(_json.dumps(result_obj, indent=2))
    tool_lines.append("")

    full_tool_text = ""
    for ch in "\n".join(tool_lines):
        full_tool_text += ch
        tool_container.code(full_tool_text, language="")
        time.sleep(0.015)

    st.markdown("---")

    # 4. 最终结果展示（SymPy）
    time.sleep(1.2)
    st.markdown("#### ✨ Final Result")
    result_container = st.empty()

    final_result = (
        "✅ SymPy Solution Complete!\n\n"
        "Equation:\n"
        "x² + 5x + 6 = 0\n\n"
        "SymPy solve(...) returned:\n"
        "  → [-2, -3]\n\n"
        "Verification:\n"
        "  • For x = -2:  4 - 10 + 6 = 0 ✓\n"
        "  • For x = -3:  9 - 15 + 6 = 0 ✓\n\n"
        "Final answer:\n"
        "x₁ = -2, x₂ = -3"
    )

    shown = ""
    for ch in final_result:
        shown += ch
        quoted = "> " + shown.replace("\n", "\n> ")
        result_container.markdown(quoted)
        time.sleep(0.03)

    st.session_state.show_agent_streaming = False



def render_result_phase(title: str, icon: str, content: str):
    """Render result phase section"""
    st.markdown(
        f"""
    <div style="background: var(--background-secondary);
                border: 1px solid var(--border-color);
                border-radius: 1rem;
                padding: 1.5rem;
                margin: 1rem 0;">
        <h3 style="color: var(--primary-color); margin-bottom: 1rem;">
            {icon} {title}
        </h3>
        {content}
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_loading_frame():
    """中间过渡帧：空白 + loading 提示"""
    st.markdown(
        """
    <div style="height: 60vh; display: flex; flex-direction: column;
       
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 小延迟，loading 帧
    time.sleep(0.8)


def main():
    """Main application"""
    # Page configuration
    st.set_page_config(
        page_title="SciNexus",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Apply custom styles
    ui_manager = UIStyleManager()
    ui_manager.apply_main_styles()

    # Initialize session state
    initialize_session_state()

    # Sidebar - always show
    with st.sidebar:
        st.markdown("### 💬 Chat History")

        button_style = """
    <style>
    section[data-testid="stSidebar"] .stButton > button,
    div[data-testid="stVerticalBlock"] .stButton > button {
        background: #eef4ff !important;
        border: 1.5px solid rgba(37,99,235,0.23) !important;
        border-radius: 1.5rem !important;
        color: #2563eb !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 24px #2563eb14 !important;
        transition: box-shadow 0.3s, border-color 0.3s;
    }
    section[data-testid="stSidebar"] .stButton > button *,
    div[data-testid="stVerticalBlock"] .stButton > button * {
        color: #2563eb !important;
        background: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover,
    div[data-testid="stVerticalBlock"] .stButton > button:hover {
        background: #e0ecff !important;
        border-color: #60a5fa !important;
        color: #2563eb !important;
        box-shadow: 0 8px 30px #60a5fa1a !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover *,
    div[data-testid="stVerticalBlock"] .stButton > button:hover * {
        color: #2563eb !important;
    }
    div[data-testid="stVerticalBlock"] div[data-testid="stMarkdownContainer"] > p {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        line-height: 1.22 !important;
    }
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] .stMarkdown strong {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }
    section[data-testid="stSidebar"] label[data-testid="stMetricLabel"] > div > div > p {
        font-size: 2.0rem !important;
        font-weight: 800 !important;
    }
    </style>
    """
        st.markdown(button_style, unsafe_allow_html=True)

        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.processing = False
            st.session_state.selected_domain = None
            st.session_state.current_chat_id = None
            st.session_state.show_streaming = False
            st.session_state.show_agent_streaming = False
            st.session_state.pending_streaming = False
            st.session_state.force_welcome = True
            st.session_state.streaming_snapshot = None
            st.rerun()

        for chat_entry in st.session_state.chat_history:
            chat_id = chat_entry["id"]
            if chat_entry["messages"]:
                first_message_content = chat_entry["messages"][0]["content"]
                display_name = f"Chat {chat_id}: {first_message_content[:20]}"
            else:
                display_name = f"Chat {chat_id}: 新对话"
            if st.sidebar.button(
                display_name,
                key=f"chat_history_{chat_id}",
                use_container_width=True,
            ):
                st.session_state.messages = chat_entry["messages"]
                st.session_state.current_chat_id = chat_id
                st.session_state.force_welcome = False
                st.session_state.streaming_snapshot = None
                st.rerun()
        
        # hide statistics
        # st.markdown("---")
        # st.markdown("### 📊 Statistics")
        # total_tools = sum(len(tools) for tools in TOOL_CATALOG.values())
        # st.metric("Domains", len(TOOL_CATALOG))
        # st.metric("Tools", total_tools)

    # Main content
    # 1. 上方 Try Example 的流式演示（打字机 + 工具调用）
    if st.session_state.show_streaming:
        render_streaming_response()

    # 1b. 动画完成后的静态快照
    elif st.session_state.streaming_snapshot:
        render_streaming_snapshot(st.session_state.streaming_snapshot)

    # 2. 底部聊天输入触发的 Agent 完整流程静态演示
    elif st.session_state.show_agent_streaming:
        render_agent_streaming_response()

    # 3. 首次进入，没有消息 → 显示欢迎页面（带占位容器）
    elif not st.session_state.messages and (
        st.session_state.force_welcome
        or not any(chat["messages"] for chat in st.session_state.chat_history)
    ):
        welcome_placeholder = st.empty()
        with welcome_placeholder.container():
            clicked_example = render_welcome_section()

        # 如果这一轮点击了 Try Example：
        #   - 立刻清空欢迎页
        #   - 渲染 loading
        #   - 设置 show_streaming=True，并在下一轮进入 streaming 动画
        if clicked_example:
            welcome_placeholder.empty()
            render_loading_frame()
            st.session_state.show_streaming = True
            st.session_state.force_welcome = False
            st.rerun()

    # 4. 普通聊天模式：渲染历史消息
    else:
        for message in st.session_state.messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            avatar = "👤" if role == "user" else "✨"
            with st.chat_message(role, avatar=avatar):
                st.markdown(content, unsafe_allow_html=True)

    # （此处 processing 仅保留样式占位，静态版本不会触发）
    if st.session_state.processing:
        render_processing_status("Processing your query...")

    # 底部聊天输入框：不调后端，静态演示
    query_input = st.chat_input("Ask anything...", key="chat_input")

    if query_input:
        st.session_state.force_welcome = False
        st.session_state.streaming_snapshot = None
        # 1. 把用户输入当作普通聊天气泡存起来（方便演示）
        st.session_state.messages.append({"role": "user", "content": query_input})

        update_current_chat_history()

        # 2. 开始静态演示
        st.session_state.show_agent_streaming = True
        st.session_state.processing = False  # 静态演示，不调后端
        st.rerun()


if __name__ == "__main__":
    main()
