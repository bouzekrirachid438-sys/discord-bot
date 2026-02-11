@echo off
title Karys Shop Bot - Running
color 0A
cd /d "%~dp0"
echo ====================================
echo      KARYS SHOP DISCORD BOT
echo ====================================
echo.
echo Starting bot...
echo.
echo Keep this window open!
echo The bot will stop if you close this window.
echo.
python bot.py
if errorlevel 1 (
    echo.
    echo [ERROR] Bot stopped with an error!
    echo Check the error message above.
    pause
)
