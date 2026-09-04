@echo off
chcp 65001 >nul
cd /d "%~dp0"
set NAME=zapret2-discord-youtube

echo ============================================
echo  Build %NAME%
echo ============================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python ne nayden. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    pip install pyinstaller
)

echo [1/2] Sborka exe...
pyinstaller --noconfirm --onefile --windowed --uac-admin --name "%NAME%" --collect-all customtkinter --clean run.py
if %errorlevel% neq 0 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo [2/2] Podgotovka papki...
set PKG=dist
set APP=%PKG%\%NAME%
if exist "%APP%" rmdir /s /q "%APP%"
mkdir "%APP%"

copy /Y "dist\%NAME%.exe" "%APP%\" >nul
xcopy /e /i /y config "%APP%\config" >nul
xcopy /e /i /y lists  "%APP%\lists"  >nul
xcopy /e /i /y blobs  "%APP%\blobs"  >nul
xcopy /e /i /y zapret2 "%APP%\zapret2" >nul
xcopy /e /i /y zapret2 "%APP%\zapret2" >nul
copy /Y "README.md" "%APP%\" >nul
copy /Y "LICENSE" "%APP%\" >nul

echo Ochistka...
del /q "dist\%NAME%.exe"
del /q "dist\%NAME%.zip"
del /q "%NAME%.spec"
if exist build rmdir /s /q build

echo.
echo ============================================
echo  Gotovo: dist\%NAME%\
echo ============================================
pause
