###############################################################################
# DRAIZER V2.0 - QUICK START (Windows + Docker)
# Запуск уже развернутой системы
###############################################################################

$ErrorActionPreference = "Stop"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Blue "🚀 DRAIZER V2.0 - QUICK START"
Write-Output ""

# Check if Docker is running
try {
    docker ps | Out-Null
} catch {
    Write-ColorOutput Red "❌ Docker is not running!"
    Write-Output "Please start Docker Desktop and try again."
    exit 1
}

Write-ColorOutput Yellow "Starting services..."
Write-Output ""

# Start all services
Write-Output "Starting Docker containers..."
docker-compose up -d

Write-Output ""
Write-Output "Waiting for services to initialize..."
Start-Sleep -Seconds 5

# Check status
Write-Output ""
Write-ColorOutput Green "✅ Services started!"
Write-Output ""

# Show container status
docker-compose ps

Write-Output ""
Write-ColorOutput Blue "📊 ACCESS POINTS:"
Write-Output "  API Backend:  http://localhost:8000/docs"
Write-Output "  Frontend:     Run 'npm run dev' in frontend directory"
Write-Output ""
Write-ColorOutput Blue "📈 VIEW LOGS:"
Write-Output "  All logs:     docker-compose logs -f"
Write-Output "  C-Engine:     docker logs draizer_c_engine -f"
Write-Output "  Backend:      docker logs draizer_backend -f"
Write-Output ""
Write-ColorOutput Blue "🛑 STOP:"
Write-Output "  docker-compose down"
Write-Output ""

