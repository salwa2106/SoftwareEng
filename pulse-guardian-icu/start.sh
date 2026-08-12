#!/bin/bash
echo "=========================================="
echo "  Pulse Guardian ICU - Startup Script"
echo "=========================================="

# Backend
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q
echo "Starting backend on port 8000..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Frontend
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing npm packages (first run)..."
    npm install
fi
echo "Starting frontend on port 3000..."
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "=========================================="
echo "  Backend:  http://localhost:8000/api/docs"
echo "  Frontend: http://localhost:3000"
echo "  Login:    admin / admin123"
echo "=========================================="
echo "Press Ctrl+C to stop both servers"
wait $BACKEND_PID $FRONTEND_PID
