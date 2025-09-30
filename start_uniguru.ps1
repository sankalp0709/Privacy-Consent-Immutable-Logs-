# Uniguru-LM Service Startup Script
# PowerShell script for Windows development environment

Write-Host "🚀 Starting Uniguru-LM Development Environment" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Yellow

# Check if virtual environment exists
if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Blue
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Blue
.\.venv\Scripts\Activate.ps1

# Install/upgrade dependencies
Write-Host "Installing dependencies..." -ForegroundColor Blue
pip install --upgrade pip
pip install -r requirements_uniguru.txt

# Copy environment file if .env doesn't exist
if (!(Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Blue
    Copy-Item ".env.uniguru" ".env"
    Write-Host "⚠️  Please update .env file with your actual credentials!" -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "Creating directories..." -ForegroundColor Blue
New-Item -ItemType Directory -Force -Path "audio_cache" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "temp" | Out-Null

# Check services status
Write-Host "`nChecking service dependencies..." -ForegroundColor Blue

# Check MongoDB
try {
    $mongoStatus = Test-NetConnection -ComputerName localhost -Port 27017 -InformationLevel Quiet
    if ($mongoStatus) {
        Write-Host "✅ MongoDB: Running" -ForegroundColor Green
    } else {
        Write-Host "❌ MongoDB: Not running (start with: net start MongoDB)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ MongoDB: Not accessible" -ForegroundColor Red
}

# Check Qdrant
try {
    $qdrantStatus = Test-NetConnection -ComputerName localhost -Port 6333 -InformationLevel Quiet
    if ($qdrantStatus) {
        Write-Host "✅ Qdrant: Running" -ForegroundColor Green
    } else {
        Write-Host "❌ Qdrant: Not running (start Qdrant service)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Qdrant: Not accessible" -ForegroundColor Red
}

# Check NAS connectivity
try {
    $nasPath = "\\192.168.0.94\Guruukul_DB"
    if (Test-Path $nasPath) {
        Write-Host "✅ NAS: Accessible" -ForegroundColor Green
    } else {
        Write-Host "⚠️  NAS: Path not accessible (will try to mount with credentials)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  NAS: Connection test failed (will try to mount with credentials)" -ForegroundColor Yellow
}

# Check local G: drive paths
try {
    $localQdrantPath = "G:\qdrant_data"
    if (Test-Path $localQdrantPath) {
        Write-Host "✅ Local Qdrant Data: Accessible" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Local Qdrant Data: Not found at G:\ drive" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Local G: drive not accessible" -ForegroundColor Yellow
}

# Display startup information
Write-Host "`n📋 Service Information:" -ForegroundColor Blue
Write-Host "   Port: 8080" -ForegroundColor White
Write-Host "   API Key: uniguru-dev-key-2025" -ForegroundColor White
Write-Host "   Health: http://localhost:8080/health" -ForegroundColor White
Write-Host "   Docs: http://localhost:8080/docs" -ForegroundColor White

Write-Host "`n🔧 Quick Commands:" -ForegroundColor Blue
Write-Host "   Start service: python uniguru_lm_service.py" -ForegroundColor White
Write-Host "   Run tests: python -m pytest" -ForegroundColor White
Write-Host "   Smoke test: .\smoke_test.ps1" -ForegroundColor White

# Handle Qdrant setup
if (-not $qdrantStatus) {
    Write-Host "
⚠️  Qdrant is not running. The service will work in fallback mode." -ForegroundColor Yellow
    $setupQdrant = Read-Host "Setup Qdrant now? (y/n/skip)"
    
    if ($setupQdrant -eq "y" -or $setupQdrant -eq "Y") {
        Write-Host "🎯 Running Qdrant setup helper..." -ForegroundColor Blue
        .\start_qdrant.ps1
    } elseif ($setupQdrant -eq "skip") {
        Write-Host "⚡ Continuing without Qdrant - using LLM enhancement and file fallback" -ForegroundColor Yellow
    }
}

# Prompt to start service
$startService = Read-Host "
Start Uniguru-LM service now? (y/n)"
if ($startService -eq "y" -or $startService -eq "Y") {
    Write-Host "
🚀 Starting Uniguru-LM Service..." -ForegroundColor Green
    Write-Host "📋 Service features available:" -ForegroundColor Blue
    if ($qdrantStatus) {
        Write-Host "  ✅ Vector search via Qdrant" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Vector search: File-based fallback" -ForegroundColor Yellow
    }
    Write-Host "  ✅ LLM enhancement (Ollama + Gemini)" -ForegroundColor Green
    Write-Host "  ✅ Multi-language support" -ForegroundColor Green
    Write-Host "  ✅ Reinforcement learning" -ForegroundColor Green
    Write-Host "  ✅ Comprehensive logging" -ForegroundColor Green
    Write-Host ""
    python uniguru_lm_service.py
} else {
    Write-Host "
✅ Environment ready! Run 'python uniguru_lm_service.py' to start the service." -ForegroundColor Green
}

# Final guidance
Write-Host "
🎯 Next Steps:" -ForegroundColor Blue
Write-Host "1. Update .env with your actual credentials if needed" -ForegroundColor White
Write-Host "2. Optionally setup Qdrant for vector search (or use fallback mode)" -ForegroundColor White
Write-Host "3. Test with: curl -H 'X-API-Key: uniguru-dev-key-2025' http://localhost:8080/health" -ForegroundColor White
Write-Host "4. Run smoke tests: .\smoke_test.ps1" -ForegroundColor White
Write-Host "5. For Qdrant help: .\start_qdrant.ps1" -ForegroundColor White
