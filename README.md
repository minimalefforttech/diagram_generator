# Diagram Generator

A tool for generating diagrams using LLM, with a Python backend API and web frontend.

## Project Structure

```
diagram_generator/
├── python/                  # Python package root
│   └── diagram_generator/   # Main Python package
│       ├── __init__.py
│       ├── backend/         # Backend API
│       └── ...
├── docs/                    # Documentation
├── tests/                   # Test suite
└── web/                     # Web frontend (to be added later)
```

## Installation

### Development Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/diagram_generator.git
   cd diagram_generator
   ```

2. Create a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

## Running the Application

### Backend API

Run the backend API server:

```bash
# Using the console script
diagram-generator-backend

# Or using the Python module directly
python -m uvicorn diagram_generator.backend.main:app --reload
```

The API will be available at http://localhost:8000

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
- **Web Frontend**: (Coming soon) React application in `web/`