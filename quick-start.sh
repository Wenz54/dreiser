#!/bin/bash
###############################################################################
# DRAIZER V2.0 - QUICK START (Ubuntu)
# Запуск уже развернутой системы
###############################################################################

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
C_ENGINE_DIR="$BACKEND_DIR/c_engine"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 DRAIZER V2.0 - QUICK START${NC}"
echo ""

# Check if system is deployed
if [[ ! -f "$C_ENGINE_DIR/build/draizer_engine" ]]; then
    echo -e "${YELLOW}⚠️  System not deployed. Run ./deploy.sh first${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting services...${NC}"
echo ""

# Start PostgreSQL & Redis
echo "1️⃣  Starting PostgreSQL & Redis..."
sudo systemctl start postgresql
sudo systemctl start redis-server

# Start C-Engine in background with CPU pinning
echo "2️⃣  Starting C-Engine (background, CPU 2-7)..."
cd "$C_ENGINE_DIR/build"
nohup sudo taskset -c 2-7 nice -n -20 ./draizer_engine --config ../config/engine.json > /tmp/draizer_engine.log 2>&1 &
ENGINE_PID=$!
echo "   PID: $ENGINE_PID"
echo "$ENGINE_PID" > /tmp/draizer_engine.pid

# Wait for engine to initialize
sleep 3

# Start Python Backend in background
echo "3️⃣  Starting Python Backend..."
cd "$BACKEND_DIR"
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 > /tmp/draizer_backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
echo "$BACKEND_PID" > /tmp/draizer_backend.pid

# Wait for backend to start
sleep 5

echo ""
echo -e "${GREEN}✅ All services started!${NC}"
echo ""
echo -e "${BLUE}📊 STATUS:${NC}"
echo "  C-Engine:  PID $ENGINE_PID (logs: tail -f /tmp/draizer_engine.log)"
echo "  Backend:   PID $BACKEND_PID (logs: tail -f /tmp/draizer_backend.log)"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo -e "${BLUE}🖥️  START FRONTEND:${NC}"
echo "  cd $PROJECT_ROOT/frontend"
echo "  npm run dev"
echo "  Open: http://localhost:3000"
echo ""
echo -e "${BLUE}🛑 STOP SERVICES:${NC}"
echo "  ./stop.sh"
echo ""

