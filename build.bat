@echo off
REM 一键打包 金币雨.exe
REM 用法：双击本文件即可
chcp 65001 >nul

setlocal
cd /d "%~dp0"

echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt || goto :err

echo [2/3] Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [3/3] Building exe with PyInstaller (using coin_rain.spec)...
python -m PyInstaller --noconfirm coin_rain.spec || goto :err

echo.
echo === Build succeeded: dist\金币雨.exe ===
pause
exit /b 0

:err
echo.
echo === Build FAILED ===
pause
exit /b 1
