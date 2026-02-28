#!/bin/bash

# SmartPesa - Start Script
# This will start both backend and frontend perfectly

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           🚀 SMART PESA - STARTING...                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

# Kill any existing processes
echo -e "${YELLOW}🛑 Stopping any running servers...${NC}"
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "python3 -m http.server" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✅ All servers stopped${NC}"
echo ""

# Start Backend
echo -e "${BLUE}📡 Starting Backend Server...${NC}"
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo -n "⏳ Waiting for backend"
for i in {1..10}; do
    sleep 1
    echo -n "."
done
echo ""

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend is running on http://localhost:8000${NC}"
    echo -e "   📚 API Docs: http://localhost:8000/api/docs"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start Frontend
echo -e "${BLUE}🖥️  Starting Frontend Server...${NC}"
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!
cd ..

# Wait for frontend
sleep 2

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✅ Frontend is running on http://localhost:3000${NC}"
    echo -e "   📊 Dashboard: http://localhost:3000/dashboard.html"
else
    echo -e "${RED}❌ Frontend failed to start${NC}"
    kill $FRONTEND_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           ✅ SMART PESA IS RUNNING!                        ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║                                                            ║"
echo "║   📡 Backend API:  http://localhost:8000                  ║"
echo "║   📚 API Docs:     http://localhost:8000/api/docs         ║"
echo "║   🖥️  Frontend:     http://localhost:3000                  ║"
echo "║   📊 Dashboard:    http://localhost:3000/dashboard.html   ║"
echo "║                                                            ║"
echo "║   📧 Default Login: test@example.com                      ║"
echo "║   🔑 Password:      password123                            ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to stop all servers"

# Handle shutdown
trap 'echo ""; echo "🛑 Stopping servers..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT TERM
wait
