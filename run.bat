@echo off
title AI Image Background Remover
echo ==========================================
echo    AI Image Background Remover (rembg)
echo ==========================================
echo.
echo [*] Checking images in 'input' folder...
python "%~dp0processor.py"
echo.
echo [*] Done! Check the 'output' folder for results.
pause
