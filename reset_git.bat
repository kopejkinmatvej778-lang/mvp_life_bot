@echo off
echo ==========================================
echo RESETTING GIT & DEPLOYING v4.0 (CLEAN)
echo ==========================================

:: 1. Удаляем папку .git (стираем историю локально)
if exist ".git" (
    echo Removing old Git history...
    rmdir /s /q ".git"
)

:: 2. Инициализируем новый репозиторий
echo Initializing fresh Git...
git init
git branch -M main

:: 3. Добавляем файлы
echo Adding files...
git add .

:: 4. Коммитим
echo Committing v4.0 Core...
git commit -m "MVP Life OS v4.0: Clean Slate"

:: 5. Подключаем удаленные репозитории (Amvera & GitHub)
echo Adding Remotes...
git remote add origin https://github.com/kopejkinmatvej778-lang/mvp_life_bot.git
git remote add amvera https://git.amvera.ru/matf1/mvpbot

:: 6. Отправляем С ПОДМЕНОЙ ИСТОРИИ (Force Push)
echo Pushing to GitHub (FORCE)...
git push -u origin main --force

echo Pushing to Amvera (FORCE)...
git push amvera main --force

echo.
echo ==========================================
echo DONE! 
echo 1. GitHub Pages will rebuild automatically.
echo 2. Amvera will rebuild automatically.
echo 3. Wait 3 minutes and everything will be brand new.
echo ==========================================
pause
