# PowerShell Smoke Test Script for Uniguru-LM Service
# Windows-compatible version

Write-Host "🧪 Starting Uniguru-LM Smoke Tests..." -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Yellow

$baseUrl = "http://localhost:8080"
$apiKey = "uniguru-dev-key-2025"
$headers = @{
    "X-API-Key" = $apiKey
    "Content-Type" = "application/json"
}

function Test-Endpoint {
    param(
        [string]$TestName,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers,
        [string]$Body = $null
    )
    
    Write-Host "`n$TestName" -ForegroundColor Blue
    Write-Host ("=" * $TestName.Length) -ForegroundColor DarkBlue
    
    try {
        if ($Body) {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Headers $Headers -Body $Body -TimeoutSec 30
        } else {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Headers $Headers -TimeoutSec 30
        }
        
        Write-Host "✅ PASS" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Gray
        $response | ConvertTo-Json -Depth 3 | Write-Host
        
        return $true
    }
    catch {
        Write-Host "❌ FAIL" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test results tracking
$testResults = @()

# Test 1: Health Check
$result1 = Test-Endpoint -TestName "1. Health Check" -Method "GET" -Url "$baseUrl/health" -Headers @{}
$testResults += @{Test = "Health Check"; Result = $result1}

# Test 2: Service Info
$result2 = Test-Endpoint -TestName "2. Service Info" -Method "GET" -Url "$baseUrl/" -Headers @{}
$testResults += @{Test = "Service Info"; Result = $result2}

# Test 3: Stats (with API key)
$result3 = Test-Endpoint -TestName "3. Stats Endpoint" -Method "GET" -Url "$baseUrl/stats" -Headers $headers
$testResults += @{Test = "Stats"; Result = $result3}

# Test 4: Compose Endpoint (English)
$englishQuery = @{
    query = "What is artificial intelligence?"
    session_id = "test-session-1"
    user_id = "test-user"
    voice_enabled = $false
    language = "en"
    max_results = 3
} | ConvertTo-Json

$result4 = Test-Endpoint -TestName "4. Compose Endpoint (English)" -Method "POST" -Url "$baseUrl/compose" -Headers $headers -Body $englishQuery
$testResults += @{Test = "Compose (English)"; Result = $result4}

# Test 5: Compose Endpoint (Hindi)
$hindiQuery = @{
    query = "कृत्रिम बुद्धिमत्ता क्या है?"
    session_id = "test-session-2"
    user_id = "test-user"
    voice_enabled = $true
    language = "hi"
    max_results = 3
} | ConvertTo-Json

$result5 = Test-Endpoint -TestName "5. Compose Endpoint (Hindi)" -Method "POST" -Url "$baseUrl/compose" -Headers $headers -Body $hindiQuery
$testResults += @{Test = "Compose (Hindi)"; Result = $result5}

# Test 6: BHIV Integration
$bhivQuery = @{
    query = "Explain machine learning concepts"
    session_id = "bhiv-test-session"
    user_id = "bhiv-test-user"
    voice_enabled = $false
    language = "en"
    max_results = 5
} | ConvertTo-Json

$result6 = Test-Endpoint -TestName "6. BHIV Integration" -Method "POST" -Url "$baseUrl/bhiv/compose" -Headers $headers -Body $bhivQuery
$testResults += @{Test = "BHIV Integration"; Result = $result6}

# Test 7: BHIV Agent Status
$result7 = Test-Endpoint -TestName "7. BHIV Agent Status" -Method "GET" -Url "$baseUrl/bhiv/agent_status" -Headers @{}
$testResults += @{Test = "BHIV Agent Status"; Result = $result7}

# Test 8: Smoke Test Endpoint
$result8 = Test-Endpoint -TestName "8. Internal Smoke Test" -Method "POST" -Url "$baseUrl/test/smoke" -Headers @{}
$testResults += @{Test = "Internal Smoke Test"; Result = $result8}

# Test 9: Feedback Test (if we have a trace ID from previous tests)
# This is optional and depends on previous test success
if ($result4 -or $result5) {
    $feedbackData = @{
        trace_id = "mock-trace-id"
        session_id = "test-session"
        user_id = "test-user"
        rating = 4
        feedback_text = "Good response quality"
        useful = $true
    } | ConvertTo-Json
    
    $result9 = Test-Endpoint -TestName "9. Feedback Endpoint" -Method "POST" -Url "$baseUrl/feedback" -Headers $headers -Body $feedbackData
    $testResults += @{Test = "Feedback"; Result = $result9}
}

# Summary
Write-Host "`n📊 Test Results Summary" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Yellow

$passedTests = 0
$totalTests = $testResults.Count

foreach ($test in $testResults) {
    if ($test.Result) {
        Write-Host "✅ $($test.Test)" -ForegroundColor Green
        $passedTests++
    } else {
        Write-Host "❌ $($test.Test)" -ForegroundColor Red
    }
}

Write-Host "`nOverall Results:" -ForegroundColor Blue
Write-Host "Passed: $passedTests / $totalTests" -ForegroundColor $(if ($passedTests -eq $totalTests) { "Green" } else { "Yellow" })

if ($passedTests -eq $totalTests) {
    Write-Host "`n🎉 All tests passed! Uniguru-LM service is working correctly." -ForegroundColor Green
} elseif ($passedTests -gt 0) {
    Write-Host "`n⚠️  Some tests passed. Check the failed tests and ensure all dependencies are running." -ForegroundColor Yellow
} else {
    Write-Host "`n❌ All tests failed. Check if the service is running on port 8080." -ForegroundColor Red
}

Write-Host "`n🔧 Troubleshooting Tips:" -ForegroundColor Blue
Write-Host "- Ensure the service is running: python uniguru_lm_service.py" -ForegroundColor White
Write-Host "- Check if MongoDB is running: net start MongoDB" -ForegroundColor White  
Write-Host "- Check if Qdrant is accessible on port 6333" -ForegroundColor White
Write-Host "- Verify NAS connectivity and credentials in .env file" -ForegroundColor White
Write-Host "- Check logs for detailed error information" -ForegroundColor White

# Save results to file
$resultsFile = "smoke_test_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$testResults | ConvertTo-Json -Depth 2 | Out-File -FilePath $resultsFile -Encoding UTF8
Write-Host "`n📄 Results saved to: $resultsFile" -ForegroundColor Gray

Write-Host "`n✅ Smoke tests completed!" -ForegroundColor Green