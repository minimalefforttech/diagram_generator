# Initialize frontend project
Write-Host "Creating frontend project..."

# Ensure Node.js is available
$nodePath = "${env:ProgramFiles}\nodejs"
if (-not (Test-Path $nodePath)) {
    $nodePath = "${env:ProgramFiles(x86)}\nodejs"
}

if (-not (Test-Path $nodePath)) {
    Write-Error "Node.js installation not found. Please restart your computer after installing Node.js and try again."
    exit 1
}

# Add Node.js to the current session's PATH
$env:Path = "$nodePath;$env:Path"

# Verify Node.js is accessible
try {
    & "$nodePath\node.exe" --version
    Write-Host "Node.js detected and accessible"
} catch {
    Write-Error "Failed to execute Node.js. Please restart your computer and try again."
    exit 1
}

# Navigate to project root (in case script is run from different location)
Set-Location $PSScriptRoot\..

# Create frontend directory if it doesn't exist
if (-not (Test-Path frontend)) {
    New-Item -ItemType Directory -Path frontend
}

# Navigate to frontend directory
Set-Location frontend

# Initialize Vite project with React + TypeScript
Write-Host "Initializing Vite project with React and TypeScript..."
& "$nodePath\npm.cmd" create vite@latest . -- --template react-ts

# Install dependencies
Write-Host "Installing dependencies..."
& "$nodePath\npm.cmd" install

# Install additional dependencies
Write-Host "Installing additional dependencies..."
& "$nodePath\npm.cmd" install @tanstack/react-query @tanstack/react-query-devtools react-router-dom tailwindcss postcss autoprefixer @mermaid-js/mermaid-cli mermaid

# Initialize Tailwind CSS
Write-Host "Initializing Tailwind CSS..."
& "$nodePath\npx.cmd" tailwindcss init -p

Write-Host "Frontend project setup complete!"
Write-Host "You can now run 'cd frontend && npm run dev' to start the development server."
