@echo off
echo ====================================
echo   Karys Shop Bot - Setup Script
echo ====================================
echo.

echo [1/3] Installing Python packages...
pip install -r requirements.txt
echo.

echo [2/3] Checking for .env file...
if not exist .env (
    echo Creating .env file from template...
    copy env_example.txt .env
    echo.
    echo ====================================
    echo   IMPORTANT: Edit .env file and add your Discord bot token!
    echo   Get your token from: https://discord.com/developers/applications
    echo ====================================
    echo.
    pause
) else (
    echo .env file already exists!
    echo.
)

echo [3/3] Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file and add your Discord bot token
echo 2. Invite bot to your server (see README.md)
echo 3. Run: python bot.py
echo.
pause
