@echo off
echo ==========================================
echo RESTORING RICH WEB APP from ARCHIVE...
echo ==========================================

:: 1. Удаляем временный minimal web_app
rmdir /s /q web_app

:: 2. Копируем старый web_app (полный)
echo Restoring Web App...
xcopy "_OLD_ARCHIVE\web_app" "web_app" /E /I /Y

:: 3. Копируем медитации (нужны для сайта)
echo Restoring Meditations...
xcopy "_OLD_ARCHIVE\meditations" "meditations" /E /I /Y

echo.
echo ==========================================
echo RESTORE COMPLETE.
echo ==========================================
pause
