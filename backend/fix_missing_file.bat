@echo off
echo [FIX] Setting up Amvera remote and pushing...

cd %~dp0

:: 1. Add remote if missing (Correct URL from previous context logs - user is mvpbot-matf1)
git remote remove amvera 2>nul
git remote add amvera https://git.amvera.ru/mvpbot-matf1/mvpbot-matf1

:: 2. Ensure config file is tracked
git add marathon_config.py
git commit -m "Fix config" 2>nul

:: 3. Push main to master (Amvera default branch)
echo Pushing to Amvera...
git push amvera main:master

echo.
echo [DONE] If it asked for password/username, enter your Amvera credentials.
pause
