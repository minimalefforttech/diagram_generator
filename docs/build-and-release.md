# Build and Release Guide

## Development Setup

1. **Clone Repository**
   ```bash
   git clone [repository-url]
   cd diagram_generator
   ```

2. **Backend Setup**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   
   # Verify setup
   pytest
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

## Development Commands

### Backend

```bash
# Run development server
python run.py

# Run tests
pytest
pytest --cov=diagram_generator

# Lint code
flake8 diagram_generator
black diagram_generator

# Type checking
mypy diagram_generator
```

### Frontend

```bash
# Run development server
cd frontend
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint
```

## Build Process

### Backend Build

1. **Create Python Package**
   ```bash
   python setup.py sdist bdist_wheel
   ```

2. **Run Pre-build Checks**
   ```bash
   # Verify tests pass
   pytest
   
   # Check coverage
   pytest --cov=diagram_generator --cov-report=html
   
   # Run linting
   flake8 diagram_generator
   black --check diagram_generator
   
   # Type checking
   mypy diagram_generator
   ```

### Frontend Build

1. **Production Build**
   ```bash
   cd frontend
   
   # Install dependencies
   npm ci
   
   # Build frontend
   npm run build
   
   # Run tests
   npm test
   
   # Check bundle size
   npm run analyze
   ```

2. **Verify Build**
   - Check dist/ directory for built files
   - Verify all assets are included
   - Test the production build locally

## Release Process

1. **Version Update**
   ```bash
   # Update version in:
   - setup.py
   - package.json
   - docs/version.txt
   ```

2. **Create Release Branch**
   ```bash
   git checkout -b release/vX.Y.Z
   git add .
   git commit -m "Release vX.Y.Z"
   ```

3. **Run Release Checks**
   ```bash
   # Backend
   pytest
   black --check diagram_generator
   flake8 diagram_generator
   mypy diagram_generator
   
   # Frontend
   cd frontend
   npm run lint
   npm test
   npm run build
   ```

4. **Build Release Packages**
   ```bash
   # Backend
   python setup.py sdist bdist_wheel
   
   # Frontend
   cd frontend && npm run build
   ```

5. **Create Distribution Package**
   ```powershell
   # Windows PowerShell
   
   # Create release directory
   mkdir release
   
   # Copy backend files
   Copy-Item "dist/*" "release/"
   Copy-Item "requirements.txt" "release/"
   
   # Copy frontend build
   Copy-Item "frontend/dist/*" "release/static/" -Recurse
   
   # Copy PlantUML
   Copy-Item "frontend/public/plantuml.jar" "release/"
   
   # Copy documentation
   Copy-Item "docs/*" "release/docs/" -Recurse
   
   # Create ZIP archive
   Compress-Archive -Path "release/*" -DestinationPath "diagram_generator_vX.Y.Z.zip"
   ```

6. **Release Checklist**
   - [ ] All tests pass
   - [ ] Code linting clean
   - [ ] Documentation updated
   - [ ] Version numbers consistent
   - [ ] PlantUML.jar included
   - [ ] Requirements.txt up to date
   - [ ] Release notes written
   - [ ] ZIP package tested on clean system

## Installation for End Users

1. **Prerequisites**
   - Verify Java installation
   - Verify Python 3.9+
   - Verify Ollama installation

2. **Installation Steps**
   ```bash
   # Extract release package
   unzip diagram_generator_vX.Y.Z.zip
   cd diagram_generator_vX.Y.Z
   
   # Create virtual environment
   python -m venv venv
   .\venv\Scripts\activate
   
   # Install requirements
   pip install -r requirements.txt
   
   # Run application
   python run.py
   ```

3. **Verify Installation**
   - Open browser to http://localhost:3000
   - Verify Ollama connectivity
   - Test diagram generation

## Troubleshooting

### Common Issues

1. **PlantUML Issues**
   - Verify Java installation
   - Check PlantUML.jar path
   - Verify Java version (11+)

2. **Ollama Connection**
   - Verify Ollama is running
   - Check localhost:11434 accessibility
   - Verify model availability

3. **Frontend Issues**
   - Clear browser cache
   - Verify WebAssembly support
   - Check console for errors

### Support Files

- Logs: `logs/diagram_generator.log`
- Config: `config/settings.json`
- Diagrams: `storage/diagrams/`
