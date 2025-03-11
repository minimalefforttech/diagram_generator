# Test integration between frontend and backend
Write-Host "Testing integration between frontend and backend..." -ForegroundColor Cyan

# Check if backend is running
try {
    $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET -ErrorAction Stop
    if ($backendResponse.StatusCode -eq 200) {
        Write-Host "✅ Backend is running at http://localhost:8000" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend is running but returned status code $($backendResponse.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Backend is not running at http://localhost:8000" -ForegroundColor Red
    Write-Host "   Start the backend with: cd python/diagram_generator; uvicorn backend.main:app --reload" -ForegroundColor Yellow
}

# Check if frontend is running
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:5173" -Method GET -ErrorAction Stop
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "✅ Frontend is running at http://localhost:5173" -ForegroundColor Green
    } else {
        Write-Host "❌ Frontend is running but returned status code $($frontendResponse.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Frontend is not running at http://localhost:5173" -ForegroundColor Red
    Write-Host "   Start the frontend with: cd frontend; npm run dev" -ForegroundColor Yellow
}

# Test API endpoints
Write-Host "`nTesting API endpoints..." -ForegroundColor Cyan

# Test diagram generation endpoint
try {
    $description = "A simple flowchart with three nodes"
    $diagram_type = "mermaid"
    
    $generateResponse = Invoke-WebRequest -Uri "http://localhost:8000/diagrams/generate?description=$description&diagram_type=$diagram_type" -Method POST -ErrorAction Stop
    if ($generateResponse.StatusCode -eq 200) {
        Write-Host "✅ Diagram generation endpoint is working" -ForegroundColor Green
        $responseContent = $generateResponse.Content | ConvertFrom-Json
        Write-Host "   Generated diagram: $($responseContent.diagram.Substring(0, [Math]::Min(50, $responseContent.diagram.Length)))..." -ForegroundColor Gray
    } else {
        Write-Host "❌ Diagram generation endpoint returned status code $($generateResponse.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to test diagram generation endpoint: $_" -ForegroundColor Red
}

# Test diagram validation endpoint
try {
    $code = "graph TD`nA[Start] --> B[End]"
    $diagram_type = "mermaid"
    
    $validateResponse = Invoke-WebRequest -Uri "http://localhost:8000/diagrams/validate?code=$code&diagram_type=$diagram_type" -Method POST -ErrorAction Stop
    if ($validateResponse.StatusCode -eq 200) {
        Write-Host "✅ Diagram validation endpoint is working" -ForegroundColor Green
        $responseContent = $validateResponse.Content | ConvertFrom-Json
        Write-Host "   Validation result: valid=$($responseContent.valid)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Diagram validation endpoint returned status code $($validateResponse.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to test diagram validation endpoint: $_" -ForegroundColor Red
}

Write-Host "`nIntegration test complete. Open http://localhost:5173 in your browser to use the application." -ForegroundColor Cyan
