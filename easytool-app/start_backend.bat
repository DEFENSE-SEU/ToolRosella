@echo off
echo Starting EasyTool FastAPI Backend...
cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8000
pause

