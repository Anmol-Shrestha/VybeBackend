#!/bin/bash

set -e

echo "🚀 Starting Restaurant Search MVP..."

# Check if backend .env exists, if not copy from example
if [ ! -f backend/.env ]; then
    echo "⚠️  backend/.env not found. Copying from .env.example"
    cp backend/.env.example backend/.env
    echo "⚠️  Please update backend/.env with your MongoDB credentials"
fi

# Install backend dependencies
if [ ! -d "backend/.venv" ] && [ ! -d "backend/venv" ]; then
    echo "📦 Installing backend dependencies with Pipenv..."
    cd backend
    pipenv install --dev
    cd ..
else
    echo "✅ Backend environment already exists"
fi

# Install frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "✅ Frontend dependencies already installed"
fi

# Start both services
echo ""
echo "🔥 Starting services..."
echo ""
echo "Frontend will be available at: http://localhost:5173"
echo "Backend will be available at: http://localhost:8000"
echo ""

# Run in parallel
(
    cd backend
    echo "Starting Backend..."
    pipenv run python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
) &
BACKEND_PID=$!

(
    cd frontend
    echo "Starting Frontend..."
    npm run dev
) &
FRONTEND_PID=$!

# Handle Ctrl+C gracefully
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" SIGINT SIGTERM

wait
