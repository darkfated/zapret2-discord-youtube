@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  zapret2-discord-youtube
echo ============================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python ne nayden. Ustanovite Python 3.10+ s python.org
    pause
    exit /b 1
)

pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    pip install pyinstaller
)

pyinstaller --noconfirm --onefile --console --name "zapret2-discord-youtube" --add-data "config;config" --add-data "lists;lists" --add-data "blobs;blobs" --add-data "zapret2;zapret2" --clean run.py

if %errorlevel% neq 0 (
    echo Build failed.
    pause
    exit /b 1
)

copy /Y "dist\zapret2-discord-youtube.exe" "." >nul 2>&1
echo Build complete: zapret2-discord-youtube.exe
pause
