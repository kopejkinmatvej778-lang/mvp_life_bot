@echo off
echo ===================================================
echo 🔄 SYNCING WITH GITHUB...
echo ===================================================
echo.
echo This script will update GitHub to match your local folder.
echo (It will DELETE files on GitHub that you deleted locally).
echo.

git add .
git commit -m "Cleanup: Removing unnecessary files"
git push origin HEAD:main

echo.
echo ===================================================
echo ✅ DONE! Check your GitHub repository.
echo ===================================================
pause
