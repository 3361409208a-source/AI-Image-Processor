@echo off
title AI Image Processor Web-UI
echo ===========================================
echo    AI Image Processor - Web Interface
echo ===========================================
echo.
echo [*] Starting Web Server...
echo [*] Please wait for the browser to open automatically.
echo.
python "%~dp0web_ui.py"
pause
