@echo off
title RAG Assistant
color 0A

echo.
echo  ============================================
echo    🧠  RAG Assistant - Document Chat App
echo  ============================================
echo.

:: Check if Ollama is running
echo  [1/3] Checking Ollama...
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo        Starting Ollama...
    start "" ollama serve
    timeout /t 3 /nobreak >nul
) else (
    echo        Ollama is running ✓
)

:: Navigate to backend folder
cd /d "%~dp0backend"

:: Start a background script that waits for server then opens browser
echo  [2/3] Starting server (please wait ~20 seconds)...
start "" cmd /c "echo Waiting for server... && :loop && timeout /t 2 /nobreak >nul && curl -s http://127.0.0.1:8000/health >nul 2>&1 && (start http://localhost:8000 && exit) || goto loop"

echo  [3/3] Server starting...
echo.
echo  ============================================
echo    Browser will open automatically when ready
echo    Press Ctrl+C to stop the server
echo  ============================================
echo.

:: Run the server (this keeps the window open)
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
