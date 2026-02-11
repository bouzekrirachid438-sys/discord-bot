@echo off
title Karys Shop Bot - Full Setup
color 0B

echo ====================================
echo   KARYS SHOP BOT - FULL SETUP
echo ====================================
echo.

echo [1/4] Installing Python packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Ma t3tach installi packages!
    pause
    exit
)
echo [OK] Packages installed!
echo.

echo [2/4] Checking Python installation...
python --version
if errorlevel 1 (
    echo [ERROR] Python ma kaynch! Khassk tinstallih.
    pause
    exit
)
echo [OK] Python installed!
echo.

echo [3/4] Creating .env file...
if exist .env (
    echo [INFO] .env file already exists!
    choice /C YN /M "Bghiti tbdl token? (Y/N)"
    if errorlevel 2 goto skip_env
)

python create_env.py
if errorlevel 1 (
    echo [ERROR] Ma t3tach dir .env file!
    pause
    exit
)

:skip_env
echo [OK] .env file ready!
echo.

echo [4/4] Setup complete!
echo.
echo ====================================
echo   NEXT STEPS:
echo ====================================
echo.
echo 1. Zid l-bot l Discord server dyalek:
echo    - Mchi l: https://discord.com/developers/applications
echo    - Dir bot jdid (shof SETUP_DARIJA.md)
echo    - Zid l-bot l server (OAuth2 ^> URL Generator)
echo.
echo 2. 7rek l-bot:
echo    - Dir: start_bot.bat
echo    - Aw: python bot.py
echo.
echo ====================================
pause
