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
   
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   
   # Install dependencies
   pip install -e ".[dev]"
   
   # Verify setup
   pytest tests/
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
python -m uvicorn diagram_generator.backend.main:app --reload

# Run tests
pytest
pytest --cov=python/diagram_generator

# Lint code
flake8 python/diagram_generator
black python/diagram_generator

# Type checking
mypy python/diagram_generator
```

### Frontend

```bash
# Run development server
cd frontend
npm run dev

# Build for production
npm run build

# Format code
npm run format

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
   pytest tests/
   
   # Check coverage
   pytest --cov=python/diagram_generator --cov-report=html
   
   # Run linting
   flake8 python/diagram_generator
   black --check python/diagram_generator
   
   # Type checking
   mypy python/diagram_generator
   ```

### Frontend Build

1. **Production Build**
   ```bash
   cd frontend
   
   # Install dependencies
   npm ci
   
   # Build frontend
   npm run build
   
   # Run linting
   npm run lint
   ```

2. **Verify Build**
   - Check dist/ directory for built files
   - Verify all assets are included
   - Test the production build: `npm run preview`

## Release Process

1. **Version Update**
   ```bash
   # Update version in:
   - setup.py
   - package.json
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
   pytest tests/
   black --check python/diagram_generator
   flake8 python/diagram_generator
   mypy python/diagram_generator
   
   # Frontend
   cd frontend
   npm run lint
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
   ```bash
   # Create release directory
   mkdir release
   
   # Copy backend files
   cp dist/* release/
   cp requirements.txt release/
   
   # Copy frontend build
   cp -r frontend/dist/* release/static/
   
   # Copy documentation
   cp -r docs/* release/docs/
   
   # Create archive
   tar -czf diagram_generator_vX.Y.Z.tar.gz release/
   ```

6. **Release Checklist**
   - [ ] All tests pass
   - [ ] Code linting clean
   - [ ] Documentation updated
   - [ ] Version numbers consistent
   - [ ] Database migrations included
   - [ ] Requirements.txt up to date
   - [ ] Release notes written
   - [ ] Package tested on clean system

## Installation for End Users

1. **Prerequisites**
   - Python 3.10 or later
   - Node.js 18 or later
   - Ollama with compatible model

2. **Installation Steps**
   ```bash
   # Extract release package
   tar -xzf diagram_generator_vX.Y.Z.tar.gz
   cd diagram_generator_vX.Y.Z
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\activate on Windows
   
   # Install package
   pip install -e .
   
   # Run application (will start both backend and frontend)
   diagram-generator
   ```

3. **Verify Installation**
   - Open browser to http://localhost:5173
   - Verify backend at http://localhost:8000/docs
   - Test diagram generation
   - Check RAG functionality
   - Verify history management

## System Verification

1. **Ollama Setup**
   ```bash
   # Verify Ollama is running
   curl http://localhost:11434/api/version
   
   # Verify model availability
   ollama list
   
   # Pull recommended model if needed
   ollama pull llama3.1:8b
   ```

2. **Database Setup**
   ```bash
   # The SQLite database will be created automatically at:
   # ~/.diagram_generator/diagrams.db
   
   # Verify database access
   sqlite3 ~/.diagram_generator/diagrams.db ".tables"
   ```

3. **RAG Verification**
   - Create a test directory with sample code
   - Enable RAG in configuration
   - Test code-aware generation
   - Verify embeddings creation

## Troubleshooting

### Common Issues

1. **Database Issues**
   - Check file permissions
   - Verify SQLite version
   - Check database path

2. **Ollama Connection**
   - Verify Ollama is running
   - Check localhost:11434 accessibility
   - Verify model installation

3. **RAG Issues**
   - Verify directory permissions 
   - Check file types being processed
   - Monitor embedding generation

4. **Frontend Issues**
   - Clear browser cache
   - Check Vite port availability
   - Monitor Chrome DevTools console

### Support Files

- Logs: `~/.diagram_generator/logs/`
- Database: `~/.diagram_generator/diagrams.db`
- RAG Cache: `~/.diagram_generator/rag_cache/`
- Config: `~/.diagram_generator/config.json`
