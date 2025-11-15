#!/bin/bash

# 激活 agenticrag 环境并启动前端
source /Users/yuanxujie/opt/anaconda3/bin/activate agenticrag

cd /Users/yuanxujie/Downloads/Easy-Tool/easytool-app/frontend

echo "=========================================="
echo "  EasyTool MCP Services - Frontend"
echo "=========================================="
echo ""
echo "Starting Streamlit app..."
echo "Open: http://localhost:8501"
echo ""

streamlit run app_mcp_showcase.py
