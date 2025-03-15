# Run both backend and frontend servers
Write-Host "Starting Diagram Generator application..." -ForegroundColor Cyan

# Function to check if a port is in use
function Test-PortInUse {
    param (
        [int]$Port
    )
    
    $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $Port }
    return $null -ne $connections
}

# Check if ports are already in use
$backendPort = 8000
$frontendPort = 5173

if (Test-PortInUse -Port $backendPort) {
    Write-Host "⚠️ Port $backendPort is already in use. Backend may already be running." -ForegroundColor Yellow
}

if (Test-PortInUse -Port $frontendPort) {
    Write-Host "⚠️ Port $frontendPort is already in use. Frontend may already be running." -ForegroundColor Yellow
}

# Navigate to project root
Set-Location $PSScriptRoot\..

# Check if Python virtual environment exists, create if not
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating Python virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Install backend in development mode if not already installed
if (-not (Get-Command diagram-generator-backend -ErrorAction SilentlyContinue)) {
    Write-Host "Installing backend in development mode..." -ForegroundColor Cyan
    pip install -e .
}

# Install frontend dependencies if node_modules doesn't exist
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    Set-Location frontend
    npm install
    Set-Location ..
}

# Start backend and frontend in separate processes
Write-Host "Starting backend server on http://localhost:$backendPort..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & .\venv\Scripts\Activate.ps1
    cd python/diagram_generator
    uvicorn backend.main:app --reload --port $using:backendPort
}

Write-Host "Starting frontend server on http://localhost:$frontendPort..." -ForegroundColor Green
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    cd frontend
    npm run dev
}

# Display output from both jobs
try {
    Write-Host "`nApplication is running!" -ForegroundColor Cyan
    Write-Host "- Backend: http://localhost:$backendPort" -ForegroundColor Cyan
    Write-Host "- Frontend: http://localhost:$frontendPort" -ForegroundColor Cyan
    Write-Host "`nPress Ctrl+C to stop both servers.`n" -ForegroundColor Yellow
    
    # Keep checking and displaying job output until user presses Ctrl+C
    while ($true) {
        $backendOutput = Receive-Job -Job $backendJob
        if ($backendOutput) {
            Write-Host "[Backend] $backendOutput" -ForegroundColor DarkGray
        }
        
        $frontendOutput = Receive-Job -Job $frontendJob
        if ($frontendOutput) {
            Write-Host "[Frontend] $frontendOutput" -ForegroundColor DarkGray
        }
        
        Start-Sleep -Seconds 1
    }
}
finally {
    # Clean up jobs when script is terminated
    Write-Host "`nStopping servers..." -ForegroundColor Cyan
    Stop-Job -Job $backendJob
    Stop-Job -Job $frontendJob
    Remove-Job -Job $backendJob
    Remove-Job -Job $frontendJob
    Write-Host "Servers stopped." -ForegroundColor Cyan
}
