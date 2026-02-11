@echo off
title Karys Shop Bot
color 0A

echo ====================================
echo      KARYS SHOP DISCORD BOT
echo ====================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] Fichier .env ma kaynch!
    echo.
    echo Khassk tdir setup d'abord:
    echo 1. Dir: python create_env.py
    echo 2. Aw dir fichier .env w kteb fih: DISCORD_BOT_TOKEN=token_dyalek
    echo.
    pause
    exit
)

REM Check if packages are installed
python -c "import discord" 2>nul
if errorlevel 1 (
    echo [INFO] Installing packages...
    python -m pip install -r requirements.txt
    echo.
)

echo [INFO] Starting bot...
echo.
python bot.py

if errorlevel 1 (
    echo.
    echo [ERROR] Bot ma khdamch!
    echo Check l-errors f l-top.
    pause
)
