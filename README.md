# Diagram Generator

A tool for generating diagrams using LLM, with a Python backend API and React frontend.

## Disclaimer

This project was purely an experiment, it is entirely generated with guidance from myself.  
Otherwise known as "vibe coding".  
Would I recommend it? No, in fact don't even credit me if you use this code.  
I do however believe that as engineers we need to explore options we disagree with in order to widen our perspective. I did in fact learn a lot about how LLMs "think" during this project and am glad to have done it regardless of how frustrating it was.

Naturally though, generated code like this has certain ethical, legal and security risks.

![Creating a new diagram](docs/screenshots/create_new_diagram.png)
![Generated Diagram](docs/screenshots/generated_diagram.png)
![Editor Panel](docs/screenshots/editor_panel.png)
![Output Log](docs/screenshots/output_log.png)

## Features

- Interactive diagram generation with a modern React frontend
- Supports both Mermaid and PlantUML diagrams
- Smart diagram generation with LLM
- Code-aware diagram generation using RAG (Retrieval Augmented Generation)
- Tool-based validation and iteration for reliable output
- Diagram history and versioning
- Clean, responsive UI with dark mode support


## Project Structure

```
diagram_generator/
├── python/                    # Python package root
│   └── diagram_generator/     # Main Python package
│       ├── backend/          # Backend API
│       │   ├── agents/      # LLM agents for diagram generation
│       │   ├── api/         # FastAPI routes and handlers
│       │   ├── core/        # Core business logic
│       │   ├── models/      # Data models and configurations
│       │   ├── services/    # External service integrations
│       │   ├── storage/     # Database and storage handlers
│       │   └── utils/       # Utility functions and helpers
│       └── services/        # Additional services
├── docs/                    # Documentation
│   ├── api/                # API documentation
│   ├── design-records/     # Design decisions and evolution
│   └── diagrams/          # Architecture diagrams
├── frontend/               # React frontend
│   ├── src/              
│   │   ├── components/    # React components
│   │   ├── contexts/      # React context providers
│   │   ├── services/      # Frontend services
│   │   └── utils/        # Frontend utilities
│   └── public/           # Static assets
├── scripts/               # Development and deployment scripts
└── tests/                # Test suites
    ├── integration/      # Integration tests
    └── unit/            # Unit tests
```

## Requirements

- Python 3.10+
- Node.js 18+
- Ollama (with at least one LLM model installed)

## Development Setup

1. Clone the repository and create virtual environment:
   ```bash
   git clone https://github.com/yourusername/diagram_generator.git
   cd diagram_generator
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. Install backend dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. Install and configure Ollama:
   - Download from [ollama.ai](https://ollama.ai)
   - Pull a compatible model:
     ```bash
     ollama pull llama3.1:8b
     ```

## Running the Application

### Quick Start (Recommended)

Run both the backend and frontend with a single command:

#### Using the CLI (After Installation)
```bash
# If you've installed the package
diagram-generator
```

#### Using Scripts (Development)

##### Windows
```powershell
# From the project root
.\scripts\run-app.ps1
```

##### macOS/Linux
```bash
# From the project root
chmod +x scripts/run-app.sh  # Make the script executable (first time only)
./scripts/run-app.sh
```

This will:
1. Create a Python virtual environment if it doesn't exist
2. Install the backend in development mode
3. Install frontend dependencies if needed
4. Start both the backend and frontend servers
5. Show combined logs from both servers

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

Press Ctrl+C to stop both servers.

The CLI provides additional options:
```bash
# Show help
diagram-generator --help

# Start only the backend
diagram-generator --backend-only

# Start only the frontend
diagram-generator --frontend-only

# Don't open browser automatically
diagram-generator --no-browser

# Use custom ports
diagram-generator --backend-port 8080 --frontend-port 3000
```

### Running Servers Separately

If you prefer to run the servers separately:

#### Backend API

```bash
# Using the console script
diagram-generator-backend

# Or using the Python module directly
python -m uvicorn diagram_generator.backend.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install  # First time only
npm run dev
```

### API Documentation

Once the backend is running, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=python/diagram_generator

# Run specific test module
pytest tests/test_main.py
```

## Project Organization

- **Backend API**: FastAPI application in `python/diagram_generator/backend/`
- **Documentation**: Project docs in `docs/`
- **Tests**: Test suite in `tests/`
- **Web Frontend**: React application with Material UI in `frontend/`
