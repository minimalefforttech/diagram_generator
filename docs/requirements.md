# System Requirements

## Required Software

1. **Operating System**
   - Cross-platform support (Windows, macOS, Linux)
   - Scripts provided for Windows (.ps1) and Unix (.sh)

2. **Python**
   - Python 3.10 or later required
   - Required for backend services and RAG processing
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify installation: `python --version`

3. **Node.js**
   - Version 18.x or later required
   - Required for frontend development
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify installation: `node --version`

4. **Ollama**
   - Required for local LLM inference and RAG embeddings
   - Must be running and accessible at http://localhost:11434
   - Installation instructions at [ollama.ai](https://ollama.ai)
   - Supported models:
     - llama3.1:8b (recommended)
     - Other compatible Llama2 models

## Hardware Requirements

- **Minimum**:
  - CPU: 4 cores
  - RAM: 16GB (for RAG processing)
  - Storage: 2GB for application + models
  
- **Recommended**:
  - CPU: 8+ cores
  - RAM: 32GB for large codebases with RAG
  - Storage: 5GB for application + models
  - GPU: NVIDIA GPU with 8GB+ VRAM (for improved LLM performance)

## Network Requirements

- Local network access for:
  - Ollama API (localhost:11434)
  - Frontend dev server (default: localhost:5173)
  - Backend API server (default: localhost:8000)

- Internet access for:
  - Initial package installation
  - Model downloads
  - Optional: External API access if configured

## Browser Requirements

- Modern web browser with ES6 and WebAssembly support
- Recommended browsers:
  - Chrome/Chromium 100+
  - Firefox 100+
  - Edge 100+
  - Safari 15+

## Dependencies

### Frontend Dependencies
- **Core**:
  - React 18+
  - TypeScript 5+
  - Vite 4+

- **UI Components**:
  - @mui/material (Material UI)
  - @emotion/react
  - @emotion/styled

- **Diagram Rendering**:
  - mermaid.js
  - plantuml-encoder

- **State Management**:
  - React Context
  - Custom hooks

### Backend Dependencies
- **Core**:
  - FastAPI
  - Uvicorn
  - Pydantic v2

- **Database**:
  - SQLite (default)
  - SQLAlchemy

- **RAG Processing**:
  - langchain
  - numpy
  - sentence-transformers
  - python-magic (file type detection)

- **Utilities**:
  - python-dotenv
  - requests
  - aiohttp
  - typing_extensions

## Storage Requirements

1. **Application Storage**
   - 100MB for application code
   - 500MB for node_modules
   - 200MB for Python virtual environment

2. **Model Storage**
   - 5GB+ for Ollama models
   - 500MB for RAG embeddings

3. **Runtime Storage**
   - 1GB+ for temporary files
   - 500MB for SQLite database
   - Additional space for large code repositories when using RAG

## Development Requirements

1. **Tools**
   - Git
   - VSCode (recommended) or similar IDE
   - Terminal with bash/powershell

2. **Environment**
   - Virtual environment support (venv)
   - npm/node package management
   - Environment variable configuration

3. **Optional Tools**
   - Docker for containerization
   - pytest for testing
   - ESLint for JavaScript/TypeScript linting
   - Prettier for code formatting
