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
    echo [ERROR] Python ne nayden. Ustanovite Python 3.10+ s python.org
    pause
    exit /b 1
)

pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    pip install pyinstaller
)

echo [1/2] Sborka exe...
pyinstaller --noconfirm --onefile --console --name "%NAME%" --clean run.py
if %errorlevel% neq 0 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo [2/2] Podgotovka paketa...
set PKG=dist\release
if exist "%PKG%" rmdir /s /q "%PKG%"
mkdir "%PKG%"

copy /Y "dist\%NAME%.exe" "%PKG%\" >nul
xcopy /e /i /y config "%PKG%\config" >nul
xcopy /e /i /y lists  "%PKG%\lists"  >nul
xcopy /e /i /y blobs  "%PKG%\blobs"  >nul
xcopy /e /i /y zapret2 "%PKG%\zapret2" >nul

powershell -NoProfile -Command "Compress-Archive -Path '%PKG%\*' -DestinationPath 'dist\%NAME%.zip' -Force"
if %errorlevel% neq 0 (
    echo [ERROR] Zip failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Gotovo: dist\%NAME%.zip
echo ============================================
pause
