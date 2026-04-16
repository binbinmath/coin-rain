@echo off
REM 一键打包 coin_rain.exe
REM 用法：双击本文件即可

setlocal
cd /d "%~dp0"

echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt || goto :err

echo [2/3] Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist coin_rain.spec del /q coin_rain.spec

echo [3/3] Building exe with PyInstaller...
python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --name coin_rain ^
  --add-data "assets/coin_drop.wav;assets" ^
  --add-data "assets/fonts;assets/fonts" ^
  --add-data "style.qss;." ^
  coin_rain.py || goto :err

echo.
echo === Build succeeded: dist\coin_rain.exe ===
pause
exit /b 0

:err
echo.
echo === Build FAILED ===
pause
exit /b 1
