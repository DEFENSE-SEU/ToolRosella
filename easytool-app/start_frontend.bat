@echo off
echo Starting EasyTool Streamlit Frontend...
cd frontend
streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501
pause

