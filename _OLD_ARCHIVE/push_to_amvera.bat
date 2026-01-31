@echo off
echo ==========================================
echo UPLOADING TO AMVERA VIA GIT...
echo ==========================================

:: Проверяем, добавлен ли удаленный репозиторий Amvera
git remote | findstr "amvera" > nul
if %errorlevel% neq 0 (
    echo Adding Amvera remote...
    git remote add amvera https://git.amvera.ru/matf1/mvpbot
)

echo.
echo Pushing code to Amvera...
git add .
git commit -m "Deployment Update: v3.0 FINAL"
git push amvera HEAD:master
git push amvera HEAD:main

echo.
echo ==========================================
echo DONE! Now go to Amvera and click "Build" if it hasn't started.
echo ==========================================
pause
