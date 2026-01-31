@echo off
echo ===================================================
echo   MVP LIFE OS v5.0 - FINAL DEPLOYMENT (AMVERA)
echo ===================================================

echo [1/5] Cleaning Git...
rmdir /s /q .git
git init

echo [2/5] Adding Files...
git add .

echo [3/5] Committing...
git commit -m "v5.0 Final Release: Elite UI + Russian Language"

echo [4/5] Adding Remote...
git remote add amvera https://amvera.io/repos/mvpbot-matf1

echo [5/5] Pushing to Amvera...
git push --force amvera master

echo.
echo ===================================================
echo   DEPLOYMENT INITIATED. CHECK AMVERA LOGS.
echo ===================================================
pause
