# IntelliPlant — Development Startup Script
Write-Host "Starting IntelliPlant..." -ForegroundColor Cyan

# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Backend
Write-Host "`n[1/2] Starting backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; pip install -r requirements.txt; uvicorn main:app --reload --port 8000" -WindowStyle Normal

Start-Sleep -Seconds 3

# Frontend
Write-Host "[2/2] Starting frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev" -WindowStyle Normal

Write-Host "`nIntelliPlant starting..." -ForegroundColor Cyan
Write-Host "  Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend UI:  http://localhost:5173" -ForegroundColor White
Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "`nSet your OpenAI API key in backend\.env before first use." -ForegroundColor Yellow
