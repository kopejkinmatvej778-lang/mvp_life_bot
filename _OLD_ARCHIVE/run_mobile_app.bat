@echo off
set REACT_NATIVE_PACKAGER_HOSTNAME=192.168.1.222
echo [MVP] STARTING DIRECT WI-FI CONNECTION...
echo.
echo =========================================================
echo SWITCHING TO LOCAL MODE (No Tunnel)
echo.
echo 1. Ensure iPhone & PC are on SAME Wi-Fi (MTS_Rtr_...)
echo 2. Scan the QR code below.
echo =========================================================
echo.
cd mvp-mobile
call npx expo start --lan
pause
