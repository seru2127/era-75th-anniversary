# ERA 75th Anniversary - Deployment Script

# Backend Setup
Write-Host "🚀 Starting ERA 75th Anniversary System..." -ForegroundColor Green

# Check if backend is running
 = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { .CommandLine -like "*uvicorn*" }
if () {
    Write-Host "✅ Backend is already running" -ForegroundColor Green
} else {
    Write-Host "❌ Backend is not running" -ForegroundColor Red
    Write-Host "   To start backend:" -ForegroundColor Yellow
    Write-Host "   cd 'C:\seru\2018\AI code\era-simple'" -ForegroundColor Yellow
    Write-Host "   .\venv\Scripts\activate" -ForegroundColor Yellow
    Write-Host "   uvicorn app:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Yellow
}

# Check if frontend is running
 = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { .CommandLine -like "*http.server*" }
if () {
    Write-Host "✅ Frontend is already running" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend is not running" -ForegroundColor Red
    Write-Host "   To start frontend:" -ForegroundColor Yellow
    Write-Host "   cd 'C:\seru\2018\AI code\era-simple'" -ForegroundColor Yellow
    Write-Host "   python -m http.server 3000" -ForegroundColor Yellow
}

Write-Host "
📋 System URLs:" -ForegroundColor Cyan
Write-Host "   Registration Form: http://localhost:3000" -ForegroundColor White
Write-Host "   Admin Dashboard:   http://localhost:3000/admin.html" -ForegroundColor White
Write-Host "   Check-in Page:     http://localhost:3000/checkin.html" -ForegroundColor White
Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   API Health:        http://localhost:8000/api/health" -ForegroundColor White

Write-Host "
📊 Database Commands:" -ForegroundColor Cyan
Write-Host "   View all: python -c "import sqlite3; conn = sqlite3.connect('registrations.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM registrations'); print(cursor.fetchall()); conn.close()"" -ForegroundColor White
