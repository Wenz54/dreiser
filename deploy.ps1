###############################################################################
# DRAIZER V2.0 - WINDOWS DEPLOYMENT SCRIPT
# Автоматическое развертывание с Docker на Windows
###############################################################################

$ErrorActionPreference = "Stop"

# Colors
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Blue "╔══════════════════════════════════════════╗"
Write-ColorOutput Blue "║   DRAIZER V2.0 - DEPLOYMENT SCRIPT      ║"
Write-ColorOutput Blue "║   Windows + Docker                       ║"
Write-ColorOutput Blue "╚══════════════════════════════════════════╝"
Write-Output ""

###############################################################################
# 1. CHECK SYSTEM REQUIREMENTS
###############################################################################

Write-ColorOutput Yellow "[1/7] Checking system requirements..."

# Check Docker
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "❌ Docker not found!"
    Write-Output "Please install Docker Desktop from:"
    Write-Output "https://www.docker.com/products/docker-desktop"
    exit 1
}

Write-ColorOutput Green "✅ Docker found"
docker --version

# Check Docker Compose
if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "❌ Docker Compose not found!"
    exit 1
}

Write-ColorOutput Green "✅ Docker Compose found"
docker-compose --version

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-ColorOutput Green "✅ Docker daemon is running"
} catch {
    Write-ColorOutput Red "❌ Docker daemon is not running!"
    Write-Output "Please start Docker Desktop and try again."
    exit 1
}

# Check disk space
$drive = (Get-Location).Drive
$freeSpace = [math]::Round((Get-PSDrive $drive.Name).Free / 1GB, 2)
Write-ColorOutput Green "✅ Free disk space: $freeSpace GB"

if ($freeSpace -lt 10) {
    Write-ColorOutput Red "❌ Less than 10GB free. Need at least 10GB."
    exit 1
}

Write-Output ""

###############################################################################
# 2. CLEAN UP OLD CONTAINERS & VOLUMES
###############################################################################

Write-ColorOutput Yellow "[2/7] Cleaning up old containers..."

# Stop running containers
Write-Output "Stopping containers..."
docker-compose down 2>$null | Out-Null

# Prune system (ONLY if user confirms)
Write-ColorOutput Yellow "⚠️  Docker cleanup will free up space but remove unused images/volumes"
$cleanup = Read-Host "Run docker system prune? (y/n)"

if ($cleanup -eq 'y') {
    Write-Output "Pruning Docker system..."
    docker system prune -f
    docker volume prune -f
    Write-ColorOutput Green "✅ Docker cleaned up"
} else {
    Write-ColorOutput Yellow "⚠️  Skipping cleanup"
}

Write-Output ""

###############################################################################
# 3. CHECK/CREATE .ENV FILE
###############################################################################

Write-ColorOutput Yellow "[3/7] Checking configuration..."

$envPath = "backend\.env"

if (!(Test-Path $envPath)) {
    Write-Output "Creating .env file..."
    
    # Generate random secrets
    $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    $encryptionKey = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    
    @"
# Database
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
POSTGRES_DB=draizer_db
POSTGRES_USER=draizer_user
POSTGRES_PASSWORD=draizer_pass_change_me

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# API Keys (IMPORTANT: Add your own!)
DEEPSEEK_API_KEY=your_deepseek_key_here
OPENAI_API_KEY=your_openai_key_here
CRYPTOPANIC_API_TOKEN=your_cryptopanic_token_here

# Security
SECRET_KEY=$secretKey
ENCRYPTION_KEY=$encryptionKey

# Trading
INITIAL_BALANCE_USD=1000
"@ | Out-File -FilePath $envPath -Encoding UTF8
    
    Write-ColorOutput Green "✅ .env file created"
    Write-ColorOutput Yellow "⚠️  IMPORTANT: Edit backend\.env and add your API keys!"
} else {
    Write-ColorOutput Green "✅ .env file exists"
}

Write-Output ""

###############################################################################
# 4. BUILD DOCKER IMAGES
###############################################################################

Write-ColorOutput Yellow "[4/7] Building Docker images..."

Write-Output "This may take 5-10 minutes on first run..."

try {
    docker-compose build --parallel 2>&1 | ForEach-Object {
        if ($_ -match "ERROR|error") {
            Write-ColorOutput Red $_
        } elseif ($_ -match "Successfully|Built") {
            Write-ColorOutput Green $_
        } else {
            Write-Output $_
        }
    }
    Write-ColorOutput Green "✅ Docker images built successfully"
} catch {
    Write-ColorOutput Red "❌ Failed to build Docker images"
    Write-ColorOutput Red $_.Exception.Message
    exit 1
}

Write-Output ""

###############################################################################
# 5. START SERVICES
###############################################################################

Write-ColorOutput Yellow "[5/7] Starting services..."

Write-Output "Starting PostgreSQL and Redis..."
docker-compose up -d postgres redis
Start-Sleep -Seconds 5

Write-Output "Running database migrations..."
docker-compose exec -T backend alembic upgrade head

Write-Output "Starting all services..."
docker-compose up -d

Write-ColorOutput Green "✅ All services started"

Write-Output ""

###############################################################################
# 6. WAIT FOR SERVICES TO BE READY
###############################################################################

Write-ColorOutput Yellow "[6/7] Waiting for services to initialize..."

$maxAttempts = 30
$attempt = 0

# Wait for C-Engine
Write-Output "Waiting for C-Engine to connect to exchanges..."
while ($attempt -lt $maxAttempts) {
    $logs = docker logs draizer_c_engine 2>&1 | Select-String "Connected" | Select-Object -Last 1
    if ($logs) {
        Write-ColorOutput Green "✅ C-Engine connected to exchanges"
        break
    }
    $attempt++
    Start-Sleep -Seconds 1
    Write-Output "." -NoNewline
}
Write-Output ""

# Wait for Backend
Write-Output "Waiting for Python Backend..."
$attempt = 0
while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput Green "✅ Python Backend is ready"
            break
        }
    } catch {}
    $attempt++
    Start-Sleep -Seconds 1
}

Write-Output ""

###############################################################################
# 7. VERIFY DEPLOYMENT
###############################################################################

Write-ColorOutput Yellow "[7/7] Verifying deployment..."

# Check container status
$containers = docker ps --format "table {{.Names}}\t{{.Status}}" | Select-String "draizer"
Write-Output "Running containers:"
Write-Output $containers

# Check C-Engine logs
Write-Output ""
Write-Output "C-Engine recent logs:"
docker logs draizer_c_engine --tail=10 2>&1

Write-Output ""

###############################################################################
# DEPLOYMENT COMPLETE
###############################################################################

Write-ColorOutput Green "╔══════════════════════════════════════════╗"
Write-ColorOutput Green "║   🎉 DEPLOYMENT COMPLETE! 🎉            ║"
Write-ColorOutput Green "╚══════════════════════════════════════════╝"
Write-Output ""

Write-ColorOutput Blue "📊 SERVICES:"
Write-Output "  C-Engine:       Running in Docker"
Write-Output "  Python Backend: http://localhost:8000"
Write-Output "  API Docs:       http://localhost:8000/docs"
Write-Output "  PostgreSQL:     localhost:5432"
Write-Output "  Redis:          localhost:6379"
Write-Output ""

Write-ColorOutput Blue "🚀 NEXT STEPS:"
Write-Output ""
Write-Output "1️⃣  Open Frontend (in new terminal):"
Write-Output "   cd frontend"
Write-Output "   npm install"
Write-Output "   npm run dev"
Write-Output ""
Write-Output "2️⃣  Access Dashboard:"
Write-Output "   http://localhost:3000"
Write-Output ""
Write-Output "3️⃣  View live logs:"
Write-Output "   docker logs draizer_c_engine -f"
Write-Output "   docker logs draizer_backend -f"
Write-Output ""

Write-ColorOutput Yellow "⚠️  IMPORTANT:"
Write-Output "  1. Edit backend\.env and add your API keys"
Write-Output "  2. Restart services after editing: docker-compose restart"
Write-Output "  3. Check C-Engine connection to Bitfinex + Deribit in logs"
Write-Output ""

Write-ColorOutput Blue "📈 MONITORING:"
Write-Output "  View all logs:       docker-compose logs -f"
Write-Output "  C-Engine only:       docker logs draizer_c_engine -f"
Write-Output "  Backend only:        docker logs draizer_backend -f"
Write-Output "  Check status:        docker-compose ps"
Write-Output "  Stop all:            docker-compose down"
Write-Output ""

Write-ColorOutput Green "✅ Happy trading! 🚀"

# Open browser (optional)
Write-Output ""
$openBrowser = Read-Host "Open API docs in browser? (y/n)"
if ($openBrowser -eq 'y') {
    Start-Process "http://localhost:8000/docs"
}

