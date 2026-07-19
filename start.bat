@echo off
echo ====================================
echo   IntelliPlant - Starting...
echo ====================================

:: Start backend (serves both API + frontend UI)
start "IntelliPlant" cmd /k "cd /d C:\Users\HP\OneDrive\Desktop\Hackathon\backend && python -m uvicorn main:app --port 8000"

:: Wait for backend to start
timeout /t 6 /nobreak > nul

:: Open browser to the single URL
start "" "http://localhost:8000"

echo.
echo ====================================
echo   IntelliPlant is running!
echo   Open: http://localhost:8000
echo ====================================
echo.
echo Close the terminal window to stop.
pause
