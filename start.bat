@echo off
chcp 65001 >nul
cd /d "%~dp0"

if exist "zapret2-discord-youtube.exe" (
    start "" "zapret2-discord-youtube.exe"
    exit /b
)

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python ne nayden.
    echo   1. Ustanovite Python 3.10+ s https://python.org
    echo   2. Zapustite build.bat dlya sozdaniya .exe
    pause
    exit /b 1
)

pip show pyyaml >nul 2>&1
if %errorlevel% neq 0 (
    pip install pyyaml
)

python run.py
