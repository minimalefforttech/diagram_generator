#!/bin/bash

set -e # Exit on error

PLANTUML_VERSION=${PLANTUML_VERSION:-v1.2024.8}
CHEERPJ_URL="https://d3415aa6bfa4.leaningtech.com/cheerpj_linux_2.3.tar.gz"

# Ensure we're in the frontend directory
cd "$(dirname "$0")/.."

echo "Setting up PlantUML with CheerpJ..."

# Create public directory if it doesn't exist
mkdir -p public

# Download and extract CheerpJ if not present
if [ ! -d "cheerpj_2.3" ]; then
    echo "Downloading CheerpJ..."
    curl -L "$CHEERPJ_URL" | tar xz || {
        echo "Failed to download or extract CheerpJ"
        exit 1
    }
    chmod +x cheerpj_2.3/cheerpjfy.py
fi

# Download PlantUML jar if needed
if [ ! -f "public/plantuml.jar" ]; then
    echo "Downloading PlantUML..."
    PLANTUML_URL="https://github.com/plantuml/plantuml/releases/download/${PLANTUML_VERSION}/plantuml.jar"
    curl -L "$PLANTUML_URL" -o public/plantuml.jar || {
        echo "Failed to download PlantUML"
        exit 1
    }
fi

# Find Python executable
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v $cmd >/dev/null 2>&1; then
        PYTHON_CMD=$cmd
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Python is required but not found in PATH"
    exit 1
fi

# Compile PlantUML with CheerpJ
echo "Compiling PlantUML with CheerpJ..."
$PYTHON_CMD cheerpj_2.3/cheerpjfy.py public/plantuml.jar || {
    echo "Failed to compile PlantUML"
    exit 1
}

# Copy CheerpJ runtime files to public directory
echo "Setting up CheerpJ runtime..."
cp -r cheerpj_2.3/cheerpj/* public/

# Rename the compiled jar to plantuml.js
mv public/plantuml.jar.js public/plantuml.js

echo "Setup complete! PlantUML is ready to use in the browser."
