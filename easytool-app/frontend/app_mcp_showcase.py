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
            "description": "Symbolic mathematics - solve equations, derivatives, integrals",
            "example": "Solve the equation x^2 - 5*x + 6 = 0",
            "icon": "📐",
        },
    ],
    "Sentiment Analysis": [
        {
            "name": "VADER Sentiment",
            "description": "Analyze text sentiment - positive, negative, neutral",
            "example": "Analyze sentiment: I absolutely love this product! It's amazing!",
            "icon": "💭",
        },
    ],
    "Chemistry & Drug Discovery": [
        {
            "name": "AiZynthFinder",
            "repo": "https://github.com/MolecularAI/aizynthfinder",
            "description": "Retrosynthetic planning - find chemical reaction routes",
            "example": "Find synthesis routes for aspirin (C9H8O4)",
            "icon": "🧪",
        },
        {
            "name": "ChemLib",
            "description": "Chemical element properties and molecular calculations",
            "example": "Calculate molecular weight of H2SO4",
            "icon": "🧪",
        },
    ],
    "Geoscience & Seismology": [
        {
            "name": "ObsPy",
            "repo": "https://github.com/obspy/obspy",
            "description": "Seismic waveform processing and earthquake analysis",
            "example": "Analyze P-wave arrival times for magnitude 6.0 earthquake",
            "icon": "🌍",
        },
    ],
    "Bioinformatics & Proteomics": [
        {
            "name": "ESM",
            "description": "Protein sequence analysis and structure prediction",
            "example": "Predict mutation effects for protein sequence with Q145G mutation",
            "icon": "🧬",
        },
        {
            "name": "SPM",
            "repo": "https://github.com/YanLab-Westlake/SPM",
            "description": "Volume-based protein sequence pattern matching",
            "example": "Match protein sequence pattern in UniProt database",
            "icon": "🧬",
        },
    ],
    "Quantum Chemistry": [
        {
            "name": "TenCirChem",
            "repo": "https://github.com/tencent-quantum-lab/TenCirChem",
            "description": "Quantum circuit simulation for molecular systems",
            "example": "Calculate ground state energy of H2 molecule using UCC",
            "icon": "⚛️",
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
        🎯 Available Tool Domains
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

                        # 写入新的“用户 query”
                        st.session_state.messages = []
                        st.session_state.messages.append(
                            {"role": "user", "content": example_query}
                        )

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
    """获取工具的演示流程（用于上面的 Try Example 区域）"""
    demo_flows = {
        "SymPy": {
            "thinking": "I will first verify if this is a valid quadratic equation in parallel, then provide the solution.",
            "tools": [
                {
                    "name": "validate_quadratic",
                    "params": {"a": "1", "b": "-5", "c": "6"},
                    "result": '{"success": true, "result": "Valid quadratic equation."}',
                },
                {
                    "name": "solve_quadratic",
                    "params": {"a": "1", "b": "-5", "c": "6"},
                    "result": '{"success": true, "result": [2, 3]}',
                },
            ],
            "result": "✅ Solution Complete!\n\nEquation: x² - 5x + 6 = 0\n\nRoots: x₁ = 2, x₂ = 3\n\nVerification:\n- When x = 2: 4 - 10 + 6 = 0 ✓\n- When x = 3: 9 - 15 + 6 = 0 ✓",
        },
        "VADER Sentiment": {
            "thinking": "I will use the VADER sentiment analyzer to analyze the emotional tendency of this review.",
            "tools": [
                {
                    "name": "analyze_sentiment",
                    "params": {
                        "text": "I absolutely love this product! It's amazing!",
                    },
                    "result": '{"success": true, "scores": {"positive": 0.87, "negative": 0.0, "neutral": 0.13, "compound": 0.94}}',
                }
            ],
            "result": "✅ Sentiment Analysis Complete!\n\nText: \"I absolutely love this product! It's amazing!\"\n\nSentiment Scores:\n  • Positive: 0.87 ⬆️\n  • Negative: 0.00\n  • Neutral: 0.13\n  • Compound: 0.94\n\nConclusion: This is a highly positive review expressing strong satisfaction with the product.",
        },
        "AiZynthFinder": {
            "thinking": "I will search for all possible synthesis routes for aspirin and evaluate their feasibility.",
            "tools": [
                {
                    "name": "search_retrosynthesis",
                    "params": {"target": "Aspirin (C9H8O4)", "depth": "3"},
                    "result": '{"success": true, "routes": 2, "best_yield": "95%"}',
                }
            ],
            "result": "✅ Retrosynthetic Analysis Complete!\n\nTarget Compound: Aspirin (C9H8O4)\n\nRecommended Synthesis Routes:\n\n【Route 1】Direct Acetylation (Optimal)\n  • Salicylic acid + Acetic anhydride → Aspirin\n  • Yield: 95%\n  • Steps: 1\n  • Reaction time: 2 hours\n\n【Route 2】Starting from Phenol\n  • Phenol + CO → Salicylic acid → Aspirin\n  • Total yield: 88%\n  • Steps: 3\n  • Total time: 8 hours",
        },
        "ObsPy": {
            "thinking": "I will process seismic waveform data and calculate epicenter parameters and propagation characteristics.",
            "tools": [
                {
                    "name": "analyze_seismic",
                    "params": {"waves": ["P", "S"], "method": "time_difference", "stations": "5"},
                    "result": '{"success": true, "magnitude": 6.0, "depth": 15.3}',
                }
            ],
            "result": "✅ Seismic Analysis Complete!\n\nEpicenter Parameters:\n  • Magnitude: 6.0 (Richter Scale)\n  • Depth: 15.3 km\n  • Distance: 52 km\n  • Latitude: 35.23°N\n  • Longitude: 139.76°E\n\nSeismic Wave Characteristics:\n  • P-wave arrival time: 2.8s\n  • S-wave arrival time: 4.9s\n  • Wave amplitude: 2.3 cm\n  • Frequency: 1.5 Hz",
        },
        "ESM": {
            "thinking": "I will use the ESM-2 language model to predict the effects of protein mutations.",
            "tools": [
                {
                    "name": "predict_mutation",
                    "params": {"protein": "example", "mutation": "Q145G"},
                    "result": '{"success": true, "effect": "MODERATE", "stability": -0.85}',
                }
            ],
            "result": "✅ Mutation Effect Prediction Complete!\n\nMutation Information:\n  • Original residue: Q (Glutamine)\n  • Mutated residue: G (Glycine)\n  • Position: 145\n\nPrediction Results:\n  • Effect level: Moderate impact\n  • ΔΔG (Stability): -0.85 kcal/mol\n  • Classification: Destabilizing\n  • Confidence: 92%\n  • Functional prediction: Likely to affect protein folding",
        },
        "TenCirChem": {
            "thinking": "I will calculate the ground state energy of the H2 molecule using the UCC method.",
            "tools": [
                {
                    "name": "ucc_energy",
                    "params": {
                        "molecule": "H2",
                        "method": "UCCSD",
                        "optimizer": "COBYLA",
                    },
                    "result": '{"success": true, "ground_state": -1.1372, "hf_energy": -1.1167}',
                }
            ],
            "result": "✅ Quantum Simulation Complete!\n\nMolecular Parameters:\n  • Molecule: H2\n  • Bond length: 0.74 Å\n  • Orbital basis: STO-3G\n\nCalculation Results:\n  • Ground state energy: -1.1372 Ha\n  • Hartree-Fock energy: -1.1167 Ha\n  • Correlation energy: -0.0205 Ha\n  • Convergence precision: 1e-6\n  • Deviation from experimental value: 0.3%",
        },
    }
    return demo_flows.get(
        tool_name,
        {
            "thinking": "处理中...",
            "tools": [],
            "result": "完成!",
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

    # 0. 显示用户查询（在最上面，逐字显示）
    time.sleep(1)
    st.markdown("#### 👤 User Query")
    query_container = st.empty()
    query_text = ""
    for char in user_query:
        query_text += char
        query_container.markdown(f"> {query_text}")
        time.sleep(0.05)
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
        # 和上面的 User Query 风格类似，使用引用块样式展示
        quoted = "> " + result_text.replace("\n", "\n> ")
        result_container.markdown(quoted)
        time.sleep(0.05)

    st.session_state.show_streaming = False


def render_agent_streaming_response():
    """底部聊天输入触发的静态 Agent 演示：
    Query -> 生成 Topics -> GitHub 搜索 & Judgement -> MCP 部署 -> Tool 调用 -> 最终结果
    """
    import json as _json

    # 固定展示的 Query
    fixed_query = "Given the equation x^2 + 5x + 6 = 0, please solve for x."

    # 0. 显示用户 Query
    time.sleep(0.8)
    st.markdown("### 🔍 SciNexus Agent Demo")
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
    st.markdown("#### 🧠 Topic Generation & GitHub Repository Search")
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

    # 2. MCP 服务部署静态演示（SymPy 版）
    time.sleep(1.0)
    st.markdown("#### 🚀 Deploy MCP Service (SymPy)")
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
    st.markdown("#### 🔧 Tool Call via MCP (SymPy)")
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

    # 4. 最终结果展示（SymPy 风格）
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

    # 小小的延迟，让用户看到 loading 帧
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
                st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Statistics")
        total_tools = sum(len(tools) for tools in TOOL_CATALOG.values())
        st.metric("Total Tools", total_tools)
        st.metric("Domains", len(TOOL_CATALOG))

    # Main content
    # 1. 上方 Try Example 的流式演示（打字机 + 工具调用）
    if st.session_state.show_streaming:
        render_streaming_response()

    # 2. 底部聊天输入触发的 Agent 完整流程静态演示
    elif st.session_state.show_agent_streaming:
        render_agent_streaming_response()

    # 3. 首次进入，没有消息 → 显示欢迎页面（带占位容器）
    elif not st.session_state.messages and not any(
        chat["messages"] for chat in st.session_state.chat_history
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
            st.rerun()

    # 4. 普通聊天模式：渲染历史消息
    else:
        for message in st.session_state.messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            avatar = "👤" if role == "user" else "✨"
            with st.chat_message(role, avatar=avatar):
                st.markdown(content, unsafe_allow_html=True)

    # （此处 processing 仅保留样式占位，当前静态版本不会触发）
    if st.session_state.processing:
        render_processing_status("Processing your query...")

    # 底部聊天输入框：不再调后端，而是触发 Agent 静态演示
    query_input = st.chat_input("Enter your task description...", key="chat_input")

    if query_input:
        # 1. 把用户输入当作普通聊天气泡存起来（方便你演示 UI）
        st.session_state.messages.append({"role": "user", "content": query_input})

        # 简单管理 chat_history
        if (
            "current_chat_id" not in st.session_state
            or st.session_state.current_chat_id is None
        ):
            new_chat_id = len(st.session_state.chat_history)
            st.session_state.chat_history.append(
                {"id": new_chat_id, "messages": st.session_state.messages.copy()}
            )
            st.session_state.current_chat_id = new_chat_id
        else:
            for chat_entry in st.session_state.chat_history:
                if chat_entry["id"] == st.session_state.current_chat_id:
                    chat_entry["messages"] = st.session_state.messages.copy()
                    break

        # 2. 开始播放 Agent 的静态演示
        st.session_state.show_agent_streaming = True
        st.session_state.processing = False  # 静态演示，不调后端
        st.rerun()


if __name__ == "__main__":
    main()
