# Start Qdrant locally for Uniguru-LM
# PowerShell script to help set up Qdrant if needed

Write-Host "🎯 Qdrant Setup Helper" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Yellow

# Check if Docker is available
$dockerAvailable = $false
try {
    $dockerVersion = docker --version
    if ($dockerVersion) {
        Write-Host "✅ Docker is available: $dockerVersion" -ForegroundColor Green
        $dockerAvailable = $true
    }
} catch {
    Write-Host "❌ Docker is not available" -ForegroundColor Red
}

# Check if Qdrant is already running
Write-Host "`n🔍 Checking if Qdrant is already running..." -ForegroundColor Blue
try {
    $qdrantStatus = Test-NetConnection -ComputerName localhost -Port 6333 -InformationLevel Quiet
    if ($qdrantStatus) {
        Write-Host "✅ Qdrant is already running on port 6333" -ForegroundColor Green
        
        # Test with curl if available
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:6333/collections" -Method Get -TimeoutSec 5
            Write-Host "✅ Qdrant API is responding" -ForegroundColor Green
            Write-Host "📦 Available collections: $($response.collections.Count)" -ForegroundColor White
            
            Write-Host "`n🎉 Qdrant is ready! You can now start Uniguru-LM:" -ForegroundColor Green
            Write-Host "   python uniguru_lm_service.py" -ForegroundColor White
            exit 0
        } catch {
            Write-Host "⚠️  Port 6333 is occupied but Qdrant API not responding" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "❌ Cannot test Qdrant connection" -ForegroundColor Red
}

# Offer solutions
Write-Host "`n🛠️  Qdrant Setup Options:" -ForegroundColor Blue

if ($dockerAvailable) {
    Write-Host "`n1️⃣  Start Qdrant with Docker (Recommended):" -ForegroundColor Green
    Write-Host "   docker run -p 6333:6333 -v `"$(pwd)/qdrant_storage:/qdrant/storage`" qdrant/qdrant" -ForegroundColor White
    
    $startDocker = Read-Host "`nStart Qdrant with Docker now? (y/n)"
    if ($startDocker -eq "y" -or $startDocker -eq "Y") {
        Write-Host "🚀 Starting Qdrant with Docker..." -ForegroundColor Green
        
        # Create storage directory
        New-Item -ItemType Directory -Force -Path "qdrant_storage" | Out-Null
        
        try {
            # Start Qdrant in detached mode
            docker run -d --name qdrant-uniguru -p 6333:6333 -v "${PWD}/qdrant_storage:/qdrant/storage" qdrant/qdrant
            
            Write-Host "✅ Qdrant container started!" -ForegroundColor Green
            Write-Host "⏳ Waiting for Qdrant to be ready..." -ForegroundColor Yellow
            
            # Wait for Qdrant to be ready
            $maxWait = 30
            $waited = 0
            do {
                Start-Sleep -Seconds 2
                $waited += 2
                try {
                    $response = Invoke-RestMethod -Uri "http://localhost:6333/collections" -Method Get -TimeoutSec 2
                    Write-Host "✅ Qdrant is ready!" -ForegroundColor Green
                    break
                } catch {
                    Write-Host "." -NoNewline -ForegroundColor Yellow
                }
            } while ($waited -lt $maxWait)
            
            if ($waited -ge $maxWait) {
                Write-Host "`n⚠️  Qdrant might still be starting. Check with: docker logs qdrant-uniguru" -ForegroundColor Yellow
            }
            
        } catch {
            Write-Host "❌ Failed to start Qdrant with Docker: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "`n2️⃣  Install Docker first:" -ForegroundColor Blue
    Write-Host "   - Download Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host "   - Or use Docker without Desktop: https://docs.docker.com/engine/install/" -ForegroundColor White
}

Write-Host "`n3️⃣  Alternative: Run Uniguru-LM without Qdrant" -ForegroundColor Blue
Write-Host "   The service will work with file-based fallback and LLM enhancement" -ForegroundColor White
Write-Host "   Just run: python uniguru_lm_service.py" -ForegroundColor White

Write-Host "`n4️⃣  Use existing Qdrant instance:" -ForegroundColor Blue
Write-Host "   Update your .env file:" -ForegroundColor White
Write-Host "   QDRANT_URL=http://your-qdrant-host:6333" -ForegroundColor White

Write-Host "`n📋 Qdrant Management Commands:" -ForegroundColor Blue
Write-Host "   Start:   docker start qdrant-uniguru" -ForegroundColor White  
Write-Host "   Stop:    docker stop qdrant-uniguru" -ForegroundColor White
Write-Host "   Remove:  docker rm qdrant-uniguru" -ForegroundColor White
Write-Host "   Logs:    docker logs qdrant-uniguru" -ForegroundColor White

Write-Host "`n🎯 Next Steps:" -ForegroundColor Green
Write-Host "1. Make sure Qdrant is running (or accept fallback mode)" -ForegroundColor White
Write-Host "2. Run: python test_config.py (to verify setup)" -ForegroundColor White
Write-Host "3. Run: python uniguru_lm_service.py" -ForegroundColor White
Write-Host "4. Test: curl -H 'X-API-Key: uniguru-dev-key-2025' http://localhost:8080/health" -ForegroundColor White