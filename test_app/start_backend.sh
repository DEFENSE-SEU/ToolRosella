#!/bin/bash

# 激活 agenticrag 环境并启动后端
source /Users/yuanxujie/opt/anaconda3/bin/activate agenticrag

cd /Users/yuanxujie/Downloads/Easy-Tool/easytool-app/backend

echo "=========================================="
echo "  EasyTool MCP Services - Backend"
echo "=========================================="
echo ""
echo "Starting FastAPI backend..."
echo "Backend URL: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""

uvicorn server_mcp_integration:app --host 0.0.0.0 --port 8000
