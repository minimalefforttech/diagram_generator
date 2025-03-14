# PowerShell script to download PlantUML jar and setup CheerpJ runtime files from CDN
param (
    [string]$PlantUMLVersion = "v1.2024.8"
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Setting up PlantUML for browser use..."

# Ensure we're in the frontend directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Split-Path -Parent $scriptDir
Set-Location $frontendDir

# Create public directory if it doesn't exist
if (-not (Test-Path "public")) {
    New-Item -ItemType Directory -Path "public" | Out-Null
}

# Create public/cheerpj directory if it doesn't exist
if (-not (Test-Path "public/cheerpj")) {
    New-Item -ItemType Directory -Path "public/cheerpj" | Out-Null
}

# Download PlantUML jar if needed
$plantumlJar = Join-Path "public" "plantuml.jar"
if (-not (Test-Path $plantumlJar)) {
    Write-Host "Downloading PlantUML jar..."
    $plantumlUrl = "https://github.com/plantuml/plantuml/releases/download/$PlantUMLVersion/plantuml.jar"
    
    try {
        Invoke-WebRequest -Uri $plantumlUrl -OutFile $plantumlJar
    }
    catch {
        Write-Error "Failed to download PlantUML jar: $_"
        exit 1
    }
}

# Download CheerpJ runtime files from CDN
$cheerpjJsUrl = "https://cjrtnc.leaningtech.com/3.0/cj3loader.js"
$cheerpjJsFile = Join-Path "public/cheerpj" "cheerpj.js"

if (-not (Test-Path $cheerpjJsFile)) {
    Write-Host "Downloading CheerpJ runtime from CDN..."
    try {
        Invoke-WebRequest -Uri $cheerpjJsUrl -OutFile $cheerpjJsFile
        
        # Create a simple worker file that just includes the main CheerpJ script
        $workerContent = "// CheerpJ worker adapter`nimportScripts('cheerpj.js');"
        $workerFile = Join-Path "public/cheerpj" "cheerpj_worker.js"
        Set-Content -Path $workerFile -Value $workerContent
    }
    catch {
        Write-Error "Failed to download CheerpJ runtime: $_"
        exit 1
    }
}

# Create a simple plantuml.js loader file
$plantumlJsFile = Join-Path "public" "plantuml.js"
if (-not (Test-Path $plantumlJsFile)) {
    Write-Host "Creating PlantUML.js loader..."
    $plantumlJsContent = @"
// PlantUML loader for browser use
(function() {
  document.addEventListener('DOMContentLoaded', async function() {
    try {
      console.log('Initializing CheerpJ for PlantUML');
      // The path to the plantuml.jar file
      const plantUmlPath = '/plantuml.jar';
      // Wait for CheerpJ to be loaded
      if (window.cheerpjInit) {
        await cheerpjInit();
        console.log('CheerpJ initialized');
      } else {
        console.error('CheerpJ not found!');
        return;
      }
      // Now tell the application that PlantUML is ready
      window.dispatchEvent(new CustomEvent('plantuml-ready'));
    } catch (error) {
      console.error('Failed to initialize PlantUML:', error);
    }
  });
})();
"@
    Set-Content -Path $plantumlJsFile -Value $plantumlJsContent
}

Write-Host "Setup complete! PlantUML is ready to use in the browser."
