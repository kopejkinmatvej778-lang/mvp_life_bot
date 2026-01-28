@echo off
cd /d "C:\Users\Егор\Desktop\MVP_Project"
echo Installing all dependencies...
python -m pip install -r requirements.txt
echo Starting bot...
python bot.py
pause
