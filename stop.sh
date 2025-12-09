#!/bin/bash
###############################################################################
# DRAIZER V2.0 - STOP SCRIPT
# Остановка всех сервисов
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Stopping DRAIZER services...${NC}"
echo ""

# Stop C-Engine
if [[ -f /tmp/draizer_engine.pid ]]; then
    ENGINE_PID=$(cat /tmp/draizer_engine.pid)
    if ps -p $ENGINE_PID > /dev/null; then
        echo "Stopping C-Engine (PID $ENGINE_PID)..."
        sudo kill -SIGTERM $ENGINE_PID 2>/dev/null || true
        sleep 2
        # Force kill if still running
        if ps -p $ENGINE_PID > /dev/null; then
            sudo kill -9 $ENGINE_PID 2>/dev/null || true
        fi
        rm /tmp/draizer_engine.pid
        echo -e "${GREEN}✅ C-Engine stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  C-Engine not running${NC}"
        rm /tmp/draizer_engine.pid
    fi
else
    echo -e "${YELLOW}⚠️  C-Engine PID file not found${NC}"
    # Try to find and kill anyway
    pkill -f "draizer_engine" 2>/dev/null || true
fi

# Stop Python Backend
if [[ -f /tmp/draizer_backend.pid ]]; then
    BACKEND_PID=$(cat /tmp/draizer_backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo "Stopping Python Backend (PID $BACKEND_PID)..."
        kill -SIGTERM $BACKEND_PID 2>/dev/null || true
        sleep 2
        if ps -p $BACKEND_PID > /dev/null; then
            kill -9 $BACKEND_PID 2>/dev/null || true
        fi
        rm /tmp/draizer_backend.pid
        echo -e "${GREEN}✅ Python Backend stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend not running${NC}"
        rm /tmp/draizer_backend.pid
    fi
else
    echo -e "${YELLOW}⚠️  Backend PID file not found${NC}"
    # Try to find and kill anyway
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
fi

# Clean shared memory
if [[ -e /dev/shm/draizer_v2 ]]; then
    echo "Cleaning shared memory..."
    sudo rm -f /dev/shm/draizer_v2
    echo -e "${GREEN}✅ Shared memory cleaned${NC}"
fi

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
echo "To start again: ./quick-start.sh"
echo ""

