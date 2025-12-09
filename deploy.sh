#!/bin/bash
###############################################################################
# DRAIZER V2.0 - UBUNTU DEPLOYMENT SCRIPT
# Автоматическое развертывание на Ubuntu Server 22.04 LTS
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
C_ENGINE_DIR="$BACKEND_DIR/c_engine"

echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DRAIZER V2.0 - DEPLOYMENT SCRIPT      ║${NC}"
echo -e "${BLUE}║   Bitfinex + Deribit Spot-Futures       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# 1. CHECK SYSTEM REQUIREMENTS
###############################################################################

echo -e "${YELLOW}[1/9] Checking system requirements...${NC}"

# Check OS
if [[ ! -f /etc/os-release ]]; then
    echo -e "${RED}❌ Cannot detect OS. This script is for Ubuntu 22.04 LTS${NC}"
    exit 1
fi

source /etc/os-release
if [[ "$ID" != "ubuntu" ]]; then
    echo -e "${YELLOW}⚠️  Warning: Not Ubuntu. Detected: $ID $VERSION${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check kernel (RT recommended but not required)
KERNEL=$(uname -r)
if [[ $KERNEL == *"rt"* ]]; then
    echo -e "${GREEN}✅ Real-Time kernel detected: $KERNEL${NC}"
else
    echo -e "${YELLOW}⚠️  Standard kernel detected: $KERNEL${NC}"
    echo -e "${YELLOW}   For best performance, install RT kernel:${NC}"
    echo -e "${YELLOW}   sudo apt install linux-image-rt-amd64${NC}"
fi

# Check CPU cores
CPU_CORES=$(nproc)
echo -e "${GREEN}✅ CPU cores: $CPU_CORES${NC}"
if [[ $CPU_CORES -lt 4 ]]; then
    echo -e "${YELLOW}⚠️  Warning: Less than 4 cores. Recommended: 8+${NC}"
fi

# Check RAM
TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
echo -e "${GREEN}✅ RAM: ${TOTAL_RAM}GB${NC}"
if [[ $TOTAL_RAM -lt 8 ]]; then
    echo -e "${YELLOW}⚠️  Warning: Less than 8GB RAM. Performance may suffer.${NC}"
fi

# Check disk space
DISK_FREE=$(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $4}' | sed 's/G//')
echo -e "${GREEN}✅ Disk space: ${DISK_FREE}GB free${NC}"
if [[ $DISK_FREE -lt 10 ]]; then
    echo -e "${RED}❌ Less than 10GB free. Need at least 10GB.${NC}"
    exit 1
fi

echo ""

###############################################################################
# 2. INSTALL SYSTEM DEPENDENCIES
###############################################################################

echo -e "${YELLOW}[2/9] Installing system dependencies...${NC}"

sudo apt update -qq

# Build tools
if ! command -v gcc &> /dev/null; then
    echo "Installing build-essential..."
    sudo apt install -y build-essential
fi

if ! command -v cmake &> /dev/null; then
    echo "Installing cmake..."
    sudo apt install -y cmake
fi

# SSL/TLS for WebSocket
if ! dpkg -l | grep -q libssl-dev; then
    echo "Installing libssl-dev..."
    sudo apt install -y libssl-dev pkg-config
fi

# PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
fi

# Redis
if ! command -v redis-cli &> /dev/null; then
    echo "Installing Redis..."
    sudo apt install -y redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
fi

# Python 3.11+
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    sudo apt install -y python3 python3-pip python3-venv
fi

# Node.js 18+ (for frontend)
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
fi

echo -e "${GREEN}✅ System dependencies installed${NC}"
echo ""

###############################################################################
# 3. INSTALL YYJSON (C JSON LIBRARY)
###############################################################################

echo -e "${YELLOW}[3/9] Installing yyjson library...${NC}"

if ! ldconfig -p | grep -q libyyjson; then
    echo "Building yyjson from source..."
    cd /tmp
    if [[ -d yyjson ]]; then
        rm -rf yyjson
    fi
    git clone https://github.com/ibireme/yyjson.git
    cd yyjson
    mkdir -p build && cd build
    cmake .. -DCMAKE_BUILD_TYPE=Release
    make -j$(nproc)
    sudo make install
    sudo ldconfig
    cd "$PROJECT_ROOT"
    echo -e "${GREEN}✅ yyjson installed${NC}"
else
    echo -e "${GREEN}✅ yyjson already installed${NC}"
fi

echo ""

###############################################################################
# 4. BUILD C-ENGINE
###############################################################################

echo -e "${YELLOW}[4/9] Building C-Engine...${NC}"

cd "$C_ENGINE_DIR"

# Clean previous build
if [[ -d build ]]; then
    echo "Cleaning previous build..."
    rm -rf build
fi

mkdir -p build
cd build

echo "Running cmake..."
cmake .. -DCMAKE_BUILD_TYPE=Release

echo "Building (using $CPU_CORES cores)..."
make -j$CPU_CORES

if [[ ! -f draizer_engine ]]; then
    echo -e "${RED}❌ Failed to build C-engine${NC}"
    exit 1
fi

# Check binary
echo ""
echo "Binary info:"
ls -lh draizer_engine
file draizer_engine

echo -e "${GREEN}✅ C-Engine built successfully${NC}"
echo ""

###############################################################################
# 5. SETUP POSTGRESQL DATABASE
###############################################################################

echo -e "${YELLOW}[5/9] Setting up PostgreSQL database...${NC}"

DB_NAME="draizer_db"
DB_USER="draizer_user"
DB_PASS="draizer_pass_$(openssl rand -hex 8)"

# Check if database exists
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo -e "${GREEN}✅ Database $DB_NAME already exists${NC}"
else
    echo "Creating database and user..."
    sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASS';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
    echo -e "${GREEN}✅ Database created${NC}"
    
    # Save credentials to .env
    cd "$BACKEND_DIR"
    if [[ ! -f .env ]]; then
        echo "Creating .env file..."
        cat > .env <<EOF
# Database
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=$DB_NAME
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASS

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# API Keys (add your own!)
DEEPSEEK_API_KEY=your_deepseek_key_here
OPENAI_API_KEY=your_openai_key_here
CRYPTOPANIC_API_TOKEN=your_cryptopanic_token_here

# Security
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)
EOF
        echo -e "${GREEN}✅ .env file created${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: Edit backend/.env and add your API keys!${NC}"
    fi
fi

echo ""

###############################################################################
# 6. SETUP PYTHON BACKEND
###############################################################################

echo -e "${YELLOW}[6/9] Setting up Python backend...${NC}"

cd "$BACKEND_DIR"

# Create virtual environment
if [[ ! -d venv ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Run database migrations
echo "Running Alembic migrations..."
alembic upgrade head

echo -e "${GREEN}✅ Python backend ready${NC}"
echo ""

###############################################################################
# 7. SETUP FRONTEND
###############################################################################

echo -e "${YELLOW}[7/9] Setting up Frontend...${NC}"

cd "$FRONTEND_DIR"

if [[ ! -d node_modules ]]; then
    echo "Installing npm dependencies..."
    npm install --silent
else
    echo -e "${GREEN}✅ npm dependencies already installed${NC}"
fi

# Build frontend for production
echo "Building frontend..."
npm run build

echo -e "${GREEN}✅ Frontend built${NC}"
echo ""

###############################################################################
# 8. APPLY SYSTEM OPTIMIZATIONS (OPTIONAL)
###############################################################################

echo -e "${YELLOW}[8/9] Applying system optimizations...${NC}"
echo "These optimizations require sudo and will improve performance."
read -p "Apply CPU tuning? (recommended for production) (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # CPU governor
    if command -v cpupower &> /dev/null; then
        sudo cpupower frequency-set -g performance 2>/dev/null || true
        echo -e "${GREEN}✅ CPU governor set to 'performance'${NC}"
    else
        sudo apt install -y linux-tools-common linux-tools-generic
        sudo cpupower frequency-set -g performance 2>/dev/null || true
    fi
    
    # Disable Turbo Boost (for stable latency)
    if [[ -f /sys/devices/system/cpu/intel_pstate/no_turbo ]]; then
        echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo > /dev/null
        echo -e "${GREEN}✅ Turbo Boost disabled (stable frequency)${NC}"
    fi
    
    # Huge Pages
    echo 2048 | sudo tee /proc/sys/vm/nr_hugepages > /dev/null
    echo -e "${GREEN}✅ Huge Pages configured (2048 pages)${NC}"
    
    # IRQ Balance
    sudo systemctl stop irqbalance 2>/dev/null || true
    sudo systemctl disable irqbalance 2>/dev/null || true
    echo -e "${GREEN}✅ IRQ Balance disabled (CPU pinning)${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping optimizations${NC}"
fi

echo ""

###############################################################################
# 9. CREATE SYSTEMD SERVICES
###############################################################################

echo -e "${YELLOW}[9/9] Creating systemd services...${NC}"

read -p "Create systemd services for auto-start? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # C-Engine service
    sudo tee /etc/systemd/system/draizer-engine.service > /dev/null <<EOF
[Unit]
Description=Draizer V2.0 C Trading Engine
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$C_ENGINE_DIR/build
ExecStart=$C_ENGINE_DIR/build/draizer_engine --config $C_ENGINE_DIR/config/engine.json
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
CPUAffinity=2-7
Nice=-20

[Install]
WantedBy=multi-user.target
EOF

    # Python Backend service
    sudo tee /etc/systemd/system/draizer-backend.service > /dev/null <<EOF
[Unit]
Description=Draizer V2.0 Python Backend
After=network.target postgresql.service redis.service draizer-engine.service
Requires=postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin:/usr/bin:/bin"
ExecStart=$BACKEND_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable services
    sudo systemctl enable draizer-engine.service
    sudo systemctl enable draizer-backend.service
    
    echo -e "${GREEN}✅ Systemd services created${NC}"
    echo ""
    echo "To start services:"
    echo "  sudo systemctl start draizer-engine"
    echo "  sudo systemctl start draizer-backend"
    echo ""
    echo "To view logs:"
    echo "  sudo journalctl -u draizer-engine -f"
    echo "  sudo journalctl -u draizer-backend -f"
else
    echo -e "${YELLOW}⚠️  Skipping systemd services${NC}"
fi

echo ""

###############################################################################
# DEPLOYMENT COMPLETE
###############################################################################

echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🎉 DEPLOYMENT COMPLETE! 🎉            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📊 SYSTEM INFO:${NC}"
echo "  Project: $PROJECT_ROOT"
echo "  C-Engine: $C_ENGINE_DIR/build/draizer_engine"
echo "  Backend: $BACKEND_DIR"
echo "  Frontend: $FRONTEND_DIR"
echo ""

echo -e "${BLUE}🚀 QUICK START:${NC}"
echo ""
echo "1️⃣  Start C-Engine (manual):"
echo "   cd $C_ENGINE_DIR/build"
echo "   sudo taskset -c 2-7 nice -n -20 ./draizer_engine --config ../config/engine.json"
echo ""
echo "2️⃣  Start Python Backend:"
echo "   cd $BACKEND_DIR"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "3️⃣  Start Frontend (development):"
echo "   cd $FRONTEND_DIR"
echo "   npm run dev"
echo ""
echo "OR use systemd services:"
echo "   sudo systemctl start draizer-engine"
echo "   sudo systemctl start draizer-backend"
echo ""

echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "  1. Edit backend/.env and add your API keys"
echo "  2. Check Bitfinex + Deribit connection in logs"
echo "  3. Open http://localhost:3000 to see dashboard"
echo ""

echo -e "${BLUE}📈 MONITORING:${NC}"
echo "  C-Engine logs:  sudo journalctl -u draizer-engine -f"
echo "  Backend logs:   sudo journalctl -u draizer-backend -f"
echo "  Check latency:  docker logs draizer_c_engine | grep LATENCY"
echo ""

echo -e "${GREEN}✅ Happy trading! 🚀${NC}"

