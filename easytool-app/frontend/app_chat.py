"""
SciNexus Chat Interface
Based on app_mcp_showcase.py but with real chat functionality
"""

import os
import sys
import json
import time
import streamlit as st
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Add current directory for UI components
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from project root
project_root = parent_dir.parent
env_file = project_root / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file, override=True)

# Import UI components
from ui_easytool import UIStyleManager, UIComponentRenderer, ToolCatalogRenderer

# Import chat modules
from chat.llm_client import LLMClient
from chat.chat_manager import ChatManager

# Multi-domain tool catalog (same as showcase)
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
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "show_welcome" not in st.session_state:
        st.session_state.show_welcome = True

    # User API configuration
    if "user_api_key" not in st.session_state:
        st.session_state.user_api_key = ""
    if "user_base_url" not in st.session_state:
        st.session_state.user_base_url = ""
    if "user_model" not in st.session_state:
        st.session_state.user_model = ""
    if "use_custom_config" not in st.session_state:
        st.session_state.use_custom_config = False

    # Initialize chat modules
    if "chat_manager" not in st.session_state:
        storage_dir = str(parent_dir / "chat_history")
        st.session_state.chat_manager = ChatManager(storage_dir=storage_dir)

    # Initialize or reinitialize LLM client based on configuration
    if "llm_client" not in st.session_state or st.session_state.get("reinit_llm", False):
        try:
            # Use user config if enabled and provided
            if st.session_state.use_custom_config and st.session_state.user_api_key:
                # Pass custom config directly to LLMClient
                st.session_state.llm_client = LLMClient(
                    api_key=st.session_state.user_api_key,
                    base_url=st.session_state.user_base_url if st.session_state.user_base_url else None,
                    model=st.session_state.user_model if st.session_state.user_model else None
                )
            else:
                # Use default .env config
                st.session_state.llm_client = LLMClient()

            st.session_state.reinit_llm = False
        except Exception as e:
            st.error(f"Failed to initialize LLM client: {e}")
            st.error("Please check your API configuration")


def start_new_chat_session():
    """Create a new chat session"""
    session_id = st.session_state.chat_manager.create_session()
    st.session_state.current_chat_id = session_id
    st.session_state.messages = []
    st.session_state.show_welcome = True


def render_welcome_section() -> bool:
    """Render welcome section with tool catalog

    Returns:
        clicked_example (bool): Whether a Try Example button was clicked
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
            <strong>Find GitHub code, convert to MCP tools, solve your tasks</strong>
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
                        # Just show a message - user can type in the chat box
                        st.info(f"💡 Example: {example_query[:100]}...\n\nPlease use the chat box below to ask your question!")
                        clicked_example = True

                    if tool != tools[-1]:
                        st.markdown("---")

    return clicked_example


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

    # Sidebar
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
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #e0ecff !important;
        border-color: #60a5fa !important;
        box-shadow: 0 8px 30px #60a5fa1a !important;
    }
    section[data-testid="stSidebar"] h3 {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }
    </style>
    """
        st.markdown(button_style, unsafe_allow_html=True)

        if st.button("➕ New Chat", use_container_width=True):
            start_new_chat_session()
            st.rerun()

        st.markdown("---")

        # List chat sessions from ChatManager
        sessions = st.session_state.chat_manager.list_sessions()
        if sessions:
            for session in sessions[:10]:  # Show last 10 sessions
                session_id = session["session_id"]
                preview = session["preview"] or "Empty chat"

                # Create a row with session button and delete button
                col1, col2 = st.columns([4, 1])

                with col1:
                    button_label = f"{preview[:25]}"
                    if st.button(
                        button_label,
                        key=f"session_{session_id}",
                        use_container_width=True,
                    ):
                        # Load this session
                        st.session_state.current_chat_id = session_id
                        st.session_state.messages = st.session_state.chat_manager.get_messages(session_id)
                        st.session_state.show_welcome = False
                        st.rerun()

                with col2:
                    if st.button("🗑️", key=f"delete_{session_id}", use_container_width=True):
                        # Delete this session
                        st.session_state.chat_manager.delete_session(session_id)
                        # If this was the current session, reset
                        if st.session_state.current_chat_id == session_id:
                            st.session_state.current_chat_id = None
                            st.session_state.messages = []
                            st.session_state.show_welcome = True
                        st.rerun()

        # API Settings at the bottom
        st.markdown("---")
        with st.expander("⚙️ API Settings", expanded=False):
            st.markdown("Configure your own API key")

            use_custom = st.checkbox(
                "Use custom API configuration",
                value=st.session_state.use_custom_config,
                key="custom_config_checkbox"
            )

            if use_custom:
                api_key = st.text_input(
                    "API Key",
                    value=st.session_state.user_api_key,
                    type="password",
                    placeholder="sk-...",
                    help="Your OpenAI API key or compatible API key"
                )

                base_url = st.text_input(
                    "Base URL (optional)",
                    value=st.session_state.user_base_url,
                    placeholder="https://api.openai.com/v1",
                    help="Leave empty to use default OpenAI endpoint"
                )

                model = st.text_input(
                    "Model (optional)",
                    value=st.session_state.user_model,
                    placeholder="gpt-4o",
                    help="Leave empty to use default model"
                )

                if st.button("💾 Save Configuration", use_container_width=True):
                    if api_key:
                        st.session_state.use_custom_config = True
                        st.session_state.user_api_key = api_key
                        st.session_state.user_base_url = base_url
                        st.session_state.user_model = model
                        st.session_state.reinit_llm = True
                        st.success("✅ Configuration saved! Reinitializing...")
                        st.rerun()
                    else:
                        st.error("API Key is required!")
            else:
                if st.session_state.use_custom_config:
                    st.session_state.use_custom_config = False
                    st.session_state.reinit_llm = True
                    st.info("Using default .env configuration")
                    st.rerun()

    # Main content area
    if st.session_state.show_welcome and not st.session_state.messages:
        # Show welcome page with examples
        render_welcome_section()
    else:
        # Chat mode - hide welcome page, show only chat messages
        # Add some top margin to avoid overlap with header
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

        # Show chat messages
        for message in st.session_state.messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            avatar = "👤" if role == "user" else "✨"
            with st.chat_message(role, avatar=avatar):
                st.markdown(content)

    # Chat input at the bottom
    if prompt := st.chat_input("Ask anything..."):
        # Hide welcome page once user starts chatting
        st.session_state.show_welcome = False

        # Create a new session if needed
        if st.session_state.current_chat_id is None:
            session_id = st.session_state.chat_manager.create_session()
            st.session_state.current_chat_id = session_id

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.chat_manager.add_message(
            st.session_state.current_chat_id,
            "user",
            prompt
        )

        # Force rerun to hide welcome page and show chat interface
        st.rerun()

    # Handle LLM response after rerun (when in chat mode)
    if not st.session_state.show_welcome and st.session_state.messages:
        # Check if the last message is from user and needs a response
        if st.session_state.messages[-1]["role"] == "user":
            # Get LLM response
            with st.chat_message("assistant", avatar="✨"):
                message_placeholder = st.empty()
                full_response = ""

                try:
                    # Stream the response
                    for chunk in st.session_state.llm_client.chat_stream(
                        messages=st.session_state.messages,
                        temperature=0.7
                    ):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")

                    message_placeholder.markdown(full_response)

                    # Add assistant response to messages
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response
                    })

                    # Save to chat manager
                    st.session_state.chat_manager.add_message(
                        st.session_state.current_chat_id,
                        "assistant",
                        full_response
                    )

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                    st.session_state.chat_manager.add_message(
                        st.session_state.current_chat_id,
                        "assistant",
                        error_msg
                    )


if __name__ == "__main__":
    main()
