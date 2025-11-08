"""
EasyTool Streamlit Frontend
Based on RepoMaster UI design patterns
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
    "Chemistry & Drug Discovery": [
        {
            "name": "AiZynthFinder",
            "repo": "https://github.com/MolecularAI/aizynthfinder",
            "description": "Retrosynthetic planning - find chemical reaction routes",
            "example": "Find synthesis routes for aspirin (C9H8O4)",
            "icon": "🧪"
        },
        {
            "name": "ChemLib",
            "description": "Chemical element properties and molecular calculations",
            "example": "Calculate molecular weight of H2SO4",
            "icon": "🧪"
        },
    ],
    "Geoscience & Seismology": [
        {
            "name": "ObsPy",
            "repo": "https://github.com/obspy/obspy",
            "description": "Seismic waveform processing and earthquake analysis",
            "example": "Analyze P-wave arrival times for magnitude 6.0 earthquake",
            "icon": "🌍"
        },
    ],
    "Bioinformatics & Proteomics": [
        {
            "name": "ESM",
            "description": "Protein sequence analysis and structure prediction",
            "example": "Predict mutation effects for protein sequence with Q145G mutation",
            "icon": "🧬"
        },
        {
            "name": "SPM",
            "repo": "https://github.com/YanLab-Westlake/SPM",
            "description": "Volume-based protein sequence pattern matching",
            "example": "Match protein sequence pattern in UniProt database",
            "icon": "🧬"
        },
    ],
    "Quantum Chemistry": [
        {
            "name": "TenCirChem",
            "repo": "https://github.com/tencent-quantum-lab/TenCirChem",
            "description": "Quantum circuit simulation for molecular systems",
            "example": "Calculate ground state energy of H2 molecule using UCC",
            "icon": "⚛️"
        },
    ],
}


def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'selected_domain' not in st.session_state:
        st.session_state.selected_domain = None


async def call_backend(query: str) -> Dict[str, Any]:
    """Call backend API"""
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(
            f"{BACKEND_URL}/run",
            json={"query": query}
        )
        response.raise_for_status()
        return response.json()


def render_welcome_section():
    """Render welcome section with tool catalog"""
    st.markdown("""
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
            <strong>Find GitHub tools, convert to MCP, solve your tasks</strong> <span style="color: #64748b;">- AI-powered agentic workflow</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <h3 style="font-size: 2.5rem; font-weight: 700; color: #1e293b; margin-bottom: 1.5rem;">
        🎯 Available Tool Domains
    </h3>
    """, unsafe_allow_html=True)
    
    cols = st.columns(2, gap="large")
    domain_list = list(TOOL_CATALOG.items())
    
    for idx, (domain, tools) in enumerate(domain_list):
        col = cols[idx % 2]
        with col:
            with st.expander(f"{tools[0]['icon']} {domain}", expanded=False):
                for tool in tools:
                    st.markdown(f"<div style='font-size: 1.35rem; font-weight: 700; margin-bottom: 0.5rem;'>{tool['name']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 1.15rem; color: #64748b; margin-bottom: 1rem;'>{tool['description']}</div>", unsafe_allow_html=True)
                    if st.button(f"▶️ Try Example", key=f"btn_{tool['name']}", use_container_width=True):
                        example_query = tool.get('example', '')
                        if 'repo' in tool:
                            example_query = f"Use {tool['repo']} to {example_query}"
                        st.session_state.messages.append({
                            'role': 'user',
                            'content': example_query
                        })
                        st.session_state.processing = True
                        st.rerun()
                    if tool != tools[-1]:
                        st.markdown("---")


def render_processing_status(status_text: str):
    """Render processing status"""
    st.markdown(f"""
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
    """, unsafe_allow_html=True)


def render_result_phase(title: str, icon: str, content: str):
    """Render result phase section"""
    st.markdown(f"""
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
    """, unsafe_allow_html=True)


def format_planning_result(plan: Dict[str, Any]) -> str:
    """Format planning phase result"""
    topics = plan.get('topics', [])
    text = plan.get('text', '')
    
    content = f"**Strategy**: {plan.get('strategy', 'topics-based')}<br>"
    if topics:
        content += f"**Generated Topics**: {', '.join(topics)}<br>"
    if text:
        content += f"**Search Keywords**: {text}"
    
    return content


def format_repo_result(data: Dict[str, Any]) -> str:
    """Format repository discovery result"""
    repo = data.get('repo', {})
    name = repo.get('name', 'Unknown')
    url = repo.get('clone_url', '')
    
    content = f"**Selected Repository**: [{name}]({url})<br>"
    content += f"**Clone URL**: `{url}`"
    
    return content


def format_conversion_result(data: Dict[str, Any]) -> str:
    """Format MCP conversion result"""
    workspace = data.get('workspace', {})
    tools = data.get('tools', [])
    
    content = f"**Status**: ✅ Successfully converted to MCP service<br>"
    content += f"**Workspace**: `{workspace.get('root', 'N/A')}`<br>"
    content += f"**MCP Entry**: `{workspace.get('start_mcp', 'N/A')}`<br><br>"
    
    if tools:
        content += f"### 🛠️ Available Tools ({len(tools)})<br>"
        for i, tool in enumerate(tools[:10], 1):
            content += f"{i}. `{tool}`<br>"
        if len(tools) > 10:
            content += f"<br>... and {len(tools) - 10} more tools"
    else:
        content += "⚠️ Tool list not available (check workspace for details)"
    
    return content


def main():
    """Main application"""
    # Page configuration
    st.set_page_config(
        page_title="SciNexus",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom styles
    ui_manager = UIStyleManager()
    ui_manager.apply_main_styles()
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📚 Quick Access")
        
        # Tool catalog in sidebar
        catalog_renderer = ToolCatalogRenderer(TOOL_CATALOG)
        catalog_renderer.render_compact_catalog()
        
        st.markdown("---")
        st.markdown("### 📊 Statistics")
        total_tools = sum(len(tools) for tools in TOOL_CATALOG.values())
        st.metric("Total Tools", total_tools)
        st.metric("Domains", len(TOOL_CATALOG))
    
    # Main content
    if not st.session_state.messages:
        render_welcome_section()
    
    # Display chat history
    for message in st.session_state.messages:
        role = message.get('role', 'user')
        content = message.get('content', '')
        avatar = "👤" if role == "user" else "✨"
        
        with st.chat_message(role, avatar=avatar):
            st.markdown(content, unsafe_allow_html=True)
    
    # Processing indicator
    if st.session_state.processing:
        render_processing_status("Processing your query...")
    
    # Chat input
    query_input = st.chat_input(
        "Enter your computational task description...",
        key="chat_input"
    )
    
    if query_input and not st.session_state.processing:
        # Add user message
        st.session_state.messages.append({
            'role': 'user',
            'content': query_input
        })
        
        # Set processing flag
        st.session_state.processing = True
        st.rerun()
    
    # Process query if flag is set
    if st.session_state.processing and st.session_state.messages:
        last_message = st.session_state.messages[-1]
        if last_message['role'] == 'user':
            query = last_message['content']
            
            try:
                # Call backend
                result = asyncio.run(call_backend(query))
                
                # Format response
                if result.get('success'):
                    response_content = ""
                    
                    # Phase 1: Planning
                    if 'plan' in result:
                        plan_content = format_planning_result(result['plan'])
                        response_content += f"""
                        <div style="margin-bottom: 1.5rem;">
                            <h4 style="color: #6366f1;">📋 Phase 1: Intelligent Planning</h4>
                            {plan_content}
                        </div>
                        """
                    
                    # Phase 2: Repository Discovery
                    if 'repo' in result:
                        repo_content = format_repo_result(result)
                        response_content += f"""
                        <div style="margin-bottom: 1.5rem;">
                            <h4 style="color: #10b981;">🎯 Phase 2: Repository Discovery</h4>
                            {repo_content}
                        </div>
                        """
                    
                    # Phase 3: Conversion
                    conversion_content = format_conversion_result(result)
                    response_content += f"""
                    <div style="margin-bottom: 1.5rem;">
                        <h4 style="color: #f59e0b;">⚙️ Phase 3: MCP Tool Conversion</h4>
                        {conversion_content}
                    </div>
                    """
                    
                    # Summary
                    workspace = result.get('workspace', {})
                    if workspace.get('start_mcp'):
                        response_content += f"""
                        <div style="background: #f0fdf4; border-left: 4px solid #10b981; 
                                    padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;">
                            <h4 style="color: #059669;">✨ Next Steps</h4>
                            <p>Run MCP service: <code>{workspace.get('start_mcp')}</code></p>
                            <p>Or deploy with Docker scripts in the deployment folder</p>
                        </div>
                        """
                else:
                    response_content = f"""
                    <div style="background: #fef2f2; border-left: 4px solid #ef4444; 
                                padding: 1rem; border-radius: 0.5rem;">
                        <h4 style="color: #dc2626;">❌ Processing Failed</h4>
                        <p>{result.get('message', 'Unknown error')}</p>
                    </div>
                    """
                
                # Add assistant message
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': response_content
                })
                
            except Exception as e:
                error_content = f"""
                <div style="background: #fef2f2; border-left: 4px solid #ef4444; 
                            padding: 1rem; border-radius: 0.5rem;">
                    <h4 style="color: #dc2626;">❌ Request Failed</h4>
                    <p>{str(e)}</p>
                </div>
                """
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': error_content
                })
            
            finally:
                # Clear processing flag
                st.session_state.processing = False
                st.rerun()


if __name__ == "__main__":
    main()

