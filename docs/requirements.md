# System Requirements

## Required Software

1. **Windows Operating System**
   - Windows 10 or later
   - Currently only supports Windows due to PlantUML.jar binary being a Windows-specific LGPL binary

2. **Java Runtime Environment**
   - Java 11 or later required
   - Required for PlantUML diagram generation
   - Installation instructions:
     1. Download JRE from [Oracle](https://www.oracle.com/java/technologies/downloads/) or use OpenJDK
     2. Add Java to system PATH
     3. Verify installation: `java -version`

3. **Node.js**
   - Version 16.x or later
   - Required for frontend development
   - Download from [nodejs.org](https://nodejs.org/)

4. **Python**
   - Python 3.9 or later
   - Required for backend services
   - Download from [python.org](https://www.python.org/downloads/)

5. **Ollama**
   - Required for local LLM inference
   - Must be running and accessible at http://localhost:11434
   - Installation instructions at [ollama.ai](https://ollama.ai)

## Hardware Requirements

- **Minimum**:
  - CPU: 4 cores
  - RAM: 8GB
  - Storage: 1GB for application, additional space for models
  
- **Recommended**:
  - CPU: 8+ cores
  - RAM: 16GB or more
  - Storage: 2GB for application, 10GB+ for models
  - GPU: NVIDIA GPU with 8GB+ VRAM (for improved LLM performance)

## Network Requirements

- Local network access for Ollama API (localhost:11434)
- Internet access for:
  - Initial package installation
  - Model downloads
  - Optional: OpenRouter API if configured

## Browser Requirements

- Modern web browser with ES6 support
- Recommended: Chrome 90+, Firefox 90+, Edge 90+
- Must support WebAssembly for diagram rendering

## Dependencies

- **Frontend**:
  - React 18+
  - Material-UI
  - Mermaid.js
  - PlantUML Viewer

- **Backend**:
  - FastAPI
  - Pydantic
  - SQLite (or PostgreSQL for production)
