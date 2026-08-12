@echo off
echo ==========================================
echo   Pulse Guardian ICU - Startup Script
echo ==========================================
echo.

echo [1/2] Starting Backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt -q
start "PulseGuardian Backend" cmd /k "venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"
cd ..

echo [2/2] Starting Frontend...
cd frontend
if not exist node_modules (
    echo Installing npm packages (first run - takes a few minutes)...
    npm install
)
start "PulseGuardian Frontend" cmd /k "npm start"
cd ..

echo.
echo ==========================================
echo   Both servers starting...
echo   Backend:  http://localhost:8000/api/docs
echo   Frontend: http://localhost:3000
echo   Login:    admin / admin123
echo ==========================================
pause
