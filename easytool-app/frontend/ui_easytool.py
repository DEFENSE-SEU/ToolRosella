"""
UI Components and Style Manager for EasyTool
Based on RepoMaster UI patterns
"""

import streamlit as st
from typing import Dict, Any, List


class UIStyleManager:
    """Centralized style management"""
    
    @staticmethod
    def apply_main_styles():
        """Apply main application styles"""
        st.markdown("""
        <style>
        /* Main theme colors */
        :root {
            --primary-color: #6366f1;
            --secondary-color: #10b981;
            --accent-color: #f59e0b;
            --background-primary: #ffffff;
            --background-secondary: #f8fafc;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            :root {
                --background-primary: #0f172a;
                --background-secondary: #1e293b;
                --text-primary: #f1f5f9;
                --text-secondary: #94a3b8;
                --border-color: #334155;
            }
        }
        
         /* Global styles */
         .main {
             padding: 0 !important;
         }
         
         #MainMenu {visibility: hidden;}
         footer {visibility: hidden;}
         
         .block-container {
             padding-top: 2rem;
             padding-bottom: 3rem;
             padding-left: 3rem;
             padding-right: 3rem;
             max-width: 1400px;
         }
        
        @media (max-width: 768px) {
            .block-container {
                padding-left: 1.5rem;
                padding-right: 1.5rem;
            }
        }
        
        /* Chat message styling */
        .stChatMessage {
            background: var(--background-secondary) !important;
            border-radius: 1rem !important;
            padding: 1rem !important;
            margin: 0.5rem 0 !important;
            border: 1px solid var(--border-color) !important;
        }
        
        .stChatMessage[data-role="user"] {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(16, 185, 129, 0.05)) !important;
        }
        
        .stChatMessage[data-role="assistant"] {
            background: var(--background-primary) !important;
        }
        
         .stButton button {
             background: linear-gradient(135deg, #6366f1, #10b981) !important;
             color: white !important;
             border: none !important;
             border-radius: 0.75rem !important;
             padding: 0.75rem 2rem !important;
             font-weight: 600 !important;
             font-size: 1.125rem !important;
             transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
             box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2) !important;
             letter-spacing: 0.01em !important;
         }
        
        .stButton button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35) !important;
            background: linear-gradient(135deg, #5558e3, #0ea770) !important;
        }
        
        .stButton button:active {
            transform: translateY(-1px) !important;
            box-shadow: 0 3px 10px rgba(99, 102, 241, 0.3) !important;
        }
        
        .stButton button[kind="secondary"] {
            background: rgba(99, 102, 241, 0.1) !important;
            color: #6366f1 !important;
            border: 1.5px solid rgba(99, 102, 241, 0.3) !important;
        }
        
        .stButton button[kind="secondary"]:hover {
            background: rgba(99, 102, 241, 0.15) !important;
            border-color: #6366f1 !important;
        }
        
         .streamlit-expanderHeader,
         details summary {
             background: transparent !important;
             background-color: transparent !important;
             border-radius: 0 !important;
             padding: 1.25rem 1.5rem !important;
             font-weight: 700 !important;
             font-size: 1.5rem !important;
             color: #1e293b !important;
             border: none !important;
             box-shadow: none !important;
             transition: none !important;
         }
         
         .streamlit-expanderHeader *,
         details summary * {
             font-size: 1.5rem !important;
             font-weight: 700 !important;
         }
         
         details {
             border: 1.5px solid #e2e8f0 !important;
             border-radius: 1rem !important;
             background: white !important;
             box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
             transition: all 0.25s ease !important;
             overflow: hidden !important;
         }
         
         details:hover {
             border-color: #6366f1 !important;
             box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12) !important;
             transform: translateY(-2px) !important;
         }
         
         details[open] {
             border-color: #e2e8f0 !important;
         }
         
         [data-testid="stSidebar"] .streamlit-expanderHeader,
         [data-testid="stSidebar"] details summary {
             font-weight: 700 !important;
             font-size: 1.2rem !important;
             border: none !important;
         }
         
         [data-testid="stSidebar"] .streamlit-expanderHeader *,
         [data-testid="stSidebar"] details summary * {
             font-size: 1.2rem !important;
             font-weight: 700 !important;
         }
         
         [data-testid="stSidebar"] details {
             border: 1.5px solid #e2e8f0 !important;
             border-radius: 1rem !important;
             background: white !important;
             box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
             transition: all 0.25s ease !important;
             overflow: hidden !important;
         }
         
         [data-testid="stSidebar"] details:hover {
             border-color: #6366f1 !important;
             box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12) !important;
             transform: translateY(-2px) !important;
         }
        
         .streamlit-expanderHeader:hover,
         details summary:hover {
             background: transparent !important;
             background-color: transparent !important;
         }
         
         details[open] summary {
             background: transparent !important;
             background-color: transparent !important;
         }
        
        .streamlit-expanderContent {
            background: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            padding: 0 1.25rem 1.25rem 1.5rem !important;
            font-size: 1.25rem !important;
        }
        
        .streamlit-expanderContent p,
        .streamlit-expanderContent div,
        .streamlit-expanderContent span,
        .streamlit-expanderContent button {
            font-size: 1.25rem !important;
        }
        
        .streamlit-expanderContent strong,
        .streamlit-expanderContent b {
            font-size: 1.35rem !important;
            font-weight: 700 !important;
        }
        
        .streamlit-expanderContent .stMarkdown {
            font-size: 1.25rem !important;
        }
        
        .streamlit-expanderContent .stButton button {
            font-size: 1.125rem !important;
        }
        
        .stMetric {
            background: white !important;
            padding: 1.25rem 1.5rem !important;
            border-radius: 1rem !important;
            border: 1.5px solid #e2e8f0 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
            transition: all 0.25s ease !important;
        }
        
        .stMetric:hover {
            border-color: #6366f1 !important;
            box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12) !important;
            transform: translateY(-2px) !important;
        }
        
        .stMetric label,
        .stMetric label *,
        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] * {
            color: #64748b !important;
            font-size: 1.5rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.02em !important;
        }
        
        .stMetric [data-testid="stMetricValue"],
        .stMetric [data-testid="stMetricValue"] * {
            color: #6366f1 !important;
            font-size: 2rem !important;
            font-weight: 700 !important;
        }
        
        
        [data-testid="stSidebar"] {
            background: #f8fafc !important;
            border-right: 1.5px solid #e2e8f0 !important;
        }
        
        [data-testid="stSidebar"] .block-container {
            padding-top: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        [data-testid="stSidebar"] h3 {
            font-size: 1.125rem !important;
            font-weight: 700 !important;
            color: #1e293b !important;
            margin-bottom: 1rem !important;
        }
        
        .stChatInput {
            border: 1.5px solid #e2e8f0 !important;
            border-radius: 1.5rem !important;
            background: white !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            overflow: hidden !important;
        }
        
        .stChatInput:focus-within {
            border-color: #3b82f6 !important;
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2) !important;
            transform: translateY(-1px) !important;
        }
        
        .stChatInput > div {
            border: none !important;
            box-shadow: none !important;
        }
        
        .stChatInput textarea {
            font-size: 1.125rem !important;
            padding: 0.75rem 1rem !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }
        
        .stChatInput textarea:focus {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }
        
        .stChatInput [data-baseweb="textarea"] {
            border: none !important;
            box-shadow: none !important;
        }
        
        /* Code block styling */
        code {
            background: var(--background-secondary) !important;
            padding: 0.2rem 0.4rem !important;
            border-radius: 0.25rem !important;
            color: var(--primary-color) !important;
            font-size: 0.9em !important;
        }
        
        pre {
            background: var(--background-secondary) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 0.5rem !important;
            padding: 1rem !important;
        }
        
        /* Link styling */
        a {
            color: var(--primary-color) !important;
            text-decoration: none !important;
            font-weight: 500 !important;
        }
        
        a:hover {
            color: var(--secondary-color) !important;
            text-decoration: underline !important;
        }
        
        /* Status badge styling */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }
        
        .status-badge.success {
            background: rgba(16, 185, 129, 0.1);
            color: #059669;
        }
        
        .status-badge.warning {
            background: rgba(245, 158, 11, 0.1);
            color: #d97706;
        }
        
        .status-badge.error {
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
        }
        
        /* Loading animation */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .loading {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        /* Card component */
        .info-card {
            background: var(--background-secondary);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        
        .info-card:hover {
            border-color: var(--primary-color);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
            transform: translateY(-2px);
        }
        
        .info-card h3 {
            color: var(--primary-color);
            margin-bottom: 0.5rem;
            font-size: 1.25rem;
        }
        
        .info-card p {
            color: var(--text-secondary);
            margin: 0;
        }
        </style>
        """, unsafe_allow_html=True)


class UIComponentRenderer:
    """Reusable UI component renderer"""
    
    @staticmethod
    def render_top_navigation(title: str, user_name: str = "Guest"):
        """Render top navigation bar"""
        st.markdown(f"""
        <div style="background: #4f46e5;
                    padding: 1.5rem 2rem;
                    margin-bottom: 2rem;
                    border-radius: 0 0 1rem 1rem;
                    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="font-size: 2rem;">🚀</div>
                    <div>
                        <h2 style="color: white; margin: 0; font-size: 1.75rem; font-weight: 700;">
                            {title}
                        </h2>
                        <p style="color: rgba(255, 255, 255, 0.9); margin: 0; font-size: 0.875rem;">
                            AI-powered computational tool platform
                        </p>
                    </div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.2);
                            padding: 0.5rem 1rem;
                            border-radius: 0.5rem;
                            color: white;
                            font-weight: 600;">
                    👤 {user_name}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_phase_card(phase_num: int, title: str, icon: str, status: str = "pending"):
        """Render processing phase card"""
        status_colors = {
            "pending": "#94a3b8",
            "processing": "#6366f1",
            "success": "#10b981",
            "error": "#ef4444"
        }
        
        status_icons = {
            "pending": "⏳",
            "processing": "🔄",
            "success": "✅",
            "error": "❌"
        }
        
        color = status_colors.get(status, status_colors["pending"])
        status_icon = status_icons.get(status, status_icons["pending"])
        
        st.markdown(f"""
        <div style="background: var(--background-secondary);
                    border-left: 4px solid {color};
                    border-radius: 0.5rem;
                    padding: 1rem;
                    margin: 0.5rem 0;
                    display: flex;
                    align-items: center;
                    gap: 1rem;">
            <div style="font-size: 1.5rem;">{icon}</div>
            <div style="flex: 1;">
                <div style="font-weight: 600; color: var(--text-primary);">
                    Phase {phase_num}: {title}
                </div>
            </div>
            <div style="font-size: 1.25rem;">{status_icon}</div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_info_box(title: str, content: str, box_type: str = "info"):
        """Render information box"""
        type_configs = {
            "info": {"color": "#6366f1", "bg": "rgba(99, 102, 241, 0.1)", "icon": "ℹ️"},
            "success": {"color": "#10b981", "bg": "rgba(16, 185, 129, 0.1)", "icon": "✅"},
            "warning": {"color": "#f59e0b", "bg": "rgba(245, 158, 11, 0.1)", "icon": "⚠️"},
            "error": {"color": "#ef4444", "bg": "rgba(239, 68, 68, 0.1)", "icon": "❌"}
        }
        
        config = type_configs.get(box_type, type_configs["info"])
        
        st.markdown(f"""
        <div style="background: {config['bg']};
                    border-left: 4px solid {config['color']};
                    border-radius: 0.5rem;
                    padding: 1rem;
                    margin: 1rem 0;">
            <div style="display: flex; align-items: start; gap: 0.75rem;">
                <div style="font-size: 1.25rem;">{config['icon']}</div>
                <div>
                    <h4 style="color: {config['color']}; margin: 0 0 0.5rem 0;">
                        {title}
                    </h4>
                    <div style="color: var(--text-primary);">
                        {content}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_tool_badge(tool_name: str, tool_type: str = "default"):
        """Render tool badge"""
        type_colors = {
            "chemistry": "#ec4899",
            "geoscience": "#10b981",
            "bioinformatics": "#6366f1",
            "quantum": "#8b5cf6",
            "default": "#64748b"
        }
        
        color = type_colors.get(tool_type.lower(), type_colors["default"])
        
        return f"""
        <span style="background: {color};
                     color: white;
                     padding: 0.25rem 0.75rem;
                     border-radius: 9999px;
                     font-size: 0.875rem;
                     font-weight: 600;
                     display: inline-block;
                     margin: 0.25rem;">
            {tool_name}
        </span>
        """


class ToolCatalogRenderer:
    """Tool catalog display component"""
    
    def __init__(self, catalog: Dict[str, List[Dict[str, Any]]]):
        self.catalog = catalog
    
    def render_compact_catalog(self):
        """Render compact catalog for sidebar"""
        for domain, tools in self.catalog.items():
            with st.expander(f"{tools[0]['icon']} {domain}", expanded=False):
                for tool in tools:
                    st.markdown(f"**{tool['name']}**")
                    st.caption(tool['description'][:60] + "..." if len(tool['description']) > 60 else tool['description'])
                    if 'example' in tool:
                        if st.button("📝 Try Example", key=f"sidebar_{tool['name']}", use_container_width=True, type="secondary"):
                            example = tool['example']
                            if 'repo' in tool:
                                example = f"Use {tool['repo']} to {example}"
                            # Add user message directly
                            st.session_state.messages.append({
                                'role': 'user',
                                'content': example
                            })
                            st.session_state.processing = True
                            st.rerun()
                    st.markdown("---")
    
    def render_full_catalog(self):
        """Render full catalog for main page"""
        for domain, tools in self.catalog.items():
            st.markdown(f"### {tools[0]['icon']} {domain}")
            
            cols = st.columns(2)
            for idx, tool in enumerate(tools):
                col = cols[idx % 2]
                with col:
                    with st.container():
                        st.markdown(f"""
                        <div class="info-card">
                            <h3>{tool['icon']} {tool['name']}</h3>
                            <p>{tool['description']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if 'example' in tool:
                            if st.button(f"▶️ Try Example", key=f"main_{tool['name']}", use_container_width=True):
                                example = tool['example']
                                if 'repo' in tool:
                                    example = f"Use {tool['repo']} to {example}"
                                # Add user message directly
                                st.session_state.messages.append({
                                    'role': 'user',
                                    'content': example
                                })
                                st.session_state.processing = True
                                st.rerun()
            
            st.markdown("---")


class ProgressTracker:
    """Track and display multi-phase progress"""
    
    def __init__(self, phases: List[str]):
        self.phases = phases
        self.current_phase = 0
        self.phase_statuses = {i: "pending" for i in range(len(phases))}
    
    def update_phase(self, phase_idx: int, status: str):
        """Update phase status"""
        self.phase_statuses[phase_idx] = status
        if status in ["success", "error"]:
            self.current_phase = phase_idx + 1
    
    def render(self):
        """Render progress tracker"""
        progress_html = '<div style="display: flex; gap: 1rem; margin: 1rem 0;">'
        
        for idx, phase in enumerate(self.phases):
            status = self.phase_statuses.get(idx, "pending")
            
            if status == "success":
                color = "#10b981"
                icon = "✅"
            elif status == "processing":
                color = "#6366f1"
                icon = "🔄"
            elif status == "error":
                color = "#ef4444"
                icon = "❌"
            else:
                color = "#94a3b8"
                icon = "⏳"
            
            progress_html += f"""
            <div style="flex: 1;
                        background: var(--background-secondary);
                        border: 2px solid {color};
                        border-radius: 0.5rem;
                        padding: 0.75rem;
                        text-align: center;">
                <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">{icon}</div>
                <div style="font-size: 0.875rem; color: {color}; font-weight: 600;">
                    {phase}
                </div>
            </div>
            """
        
        progress_html += '</div>'
        st.markdown(progress_html, unsafe_allow_html=True)

