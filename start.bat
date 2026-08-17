@echo off
title KAIRUS Server
cd /d C:\Users\gabriel\Desktop\KI\KAIRUS
call C:\Users\gabriel\Desktop\KI\.venv\Scripts\activate.bat
echo.
echo   KAIRUS v0.3.0 iniciando...
echo   http://127.0.0.1:8000
echo.
uvicorn backend.main:app --reload
pause