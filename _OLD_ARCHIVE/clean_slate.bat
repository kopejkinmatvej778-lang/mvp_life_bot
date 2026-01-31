@echo off
echo ==========================================
echo STARTING CLEAN SLATE OPERATION v4.0
echo ==========================================

if not exist "_OLD_ARCHIVE" mkdir "_OLD_ARCHIVE"

echo Moving generic files...
move *.py "_OLD_ARCHIVE" > nul 2>&1
move *.bat "_OLD_ARCHIVE" > nul 2>&1
move *.txt "_OLD_ARCHIVE" > nul 2>&1
move *.md "_OLD_ARCHIVE" > nul 2>&1
move *.yaml "_OLD_ARCHIVE" > nul 2>&1
move *.json "_OLD_ARCHIVE" > nul 2>&1

echo Moving folders...
move database "_OLD_ARCHIVE" > nul 2>&1
move handlers "_OLD_ARCHIVE" > nul 2>&1
move keyboards "_OLD_ARCHIVE" > nul 2>&1
move utils "_OLD_ARCHIVE" > nul 2>&1
move web_app "_OLD_ARCHIVE" > nul 2>&1
move meditations "_OLD_ARCHIVE" > nul 2>&1
move migrations "_OLD_ARCHIVE" > nul 2>&1
move mvp-mobile "_OLD_ARCHIVE" > nul 2>&1
move logs "_OLD_ARCHIVE" > nul 2>&1

echo Restoring Critical Secrets...
copy "_OLD_ARCHIVE\.env" ".env" > nul 2>&1

echo.
echo ==========================================
echo CLEANUP COMPLETE. WORKSPACE IS READY.
echo ==========================================
pause
