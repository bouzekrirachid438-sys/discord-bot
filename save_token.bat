@echo off
echo Enter your Discord Bot Token:
set /p TOKEN=
echo DISCORD_BOT_TOKEN=%TOKEN% > .env
echo.
echo ✅ Token saved successfully in .env file!
echo.
pause
