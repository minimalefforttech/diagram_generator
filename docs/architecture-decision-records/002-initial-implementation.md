# ADR 002: Initial Implementation Approach

## Status
In Progress - Backend Implementation Started

## Context
After outlining the LLM Diagram Generator project in ADR-001, we need to define a structured implementation approach. Key considerations include:
- Ensuring a solid backend foundation before frontend development
- Implementing robust testing from the start
- Integrating with the existing Ollama installation
- Maintaining accurate diagrams throughout development
- Creating proper development environments and setup instructions

## Decision

### Implementation Approach

We will adopt a backend-first development strategy with the following key principles:

1. **Backend Priority**: Complete and stabilize the core backend functionality before starting frontend development
2. **Test-Driven Development**: Write and run tests for each component before and during implementation
3. **Continuous Diagram Updates**: Keep all system diagrams current to reflect implementation changes
4. **Virtual Environments**: Use Python virtual environments to ensure dependency isolation
5. **Incremental Integration**: Build and test each component individually before integrating them

### Development Process

The development process will follow these steps:

1. Set up development environment with virtual environments and required dependencies
2. Implement core backend components in logical sequence
3. Write tests before implementing each feature (Test-Driven Development)
4. Update diagrams as implementation progresses
5. Document API interfaces as they are developed
6. Perform integration testing as components are connected
7. Begin frontend development only after backend components pass all tests

### Testing Strategy

1. **Unit Tests**: For individual functions and classes
2. **Integration Tests**: For component interactions, especially between:
   - LLM service and diagram generators
   - Validation services and diagram generators
   - API endpoints and backend services
3. **End-to-End Tests**: For complete workflows
4. **Diagram Validation Tests**: Specific tests to verify diagram syntax generation

### Ollama Integration

Since Ollama is already running in the environment:
1. ✅ Created abstraction layer for LLM services (OllamaService class)
2. ✅ Implemented Ollama-specific adapter with API endpoints
3. ✅ Configured connection parameters with caching support
4. ✅ Added comprehensive test suite for both service and API layers
5. 🔄 Implement fallback mechanisms for service disruptions (Pending)

### Backend Components Implementation Sequence

We will implement components in the following sequence:

1. **Core LLM Service Layer**
   - ✅ Ollama service integration
   - ✅ Model selection and management
   - ✅ Base prompt templates

2. **Diagram Generation Layer**
   - ✅ Basic diagram generation from descriptions
   - ✅ Diagram syntax validation
   - ✅ Cross-format diagram conversion
   - 🔄 Response parsing and error handling (In Progress)

2. **Diagram Validation Layer**
   - Mermaid syntax validation
   - PlantUML syntax validation
   - Diagram type detection

3. **Diagram Generation System**
   - Basic diagram generation
   - Conversion between diagram types
   - Refinement capabilities

4. **API Layer**
   - ✅ Model endpoints (Ollama integration)
   - ✅ Diagram generation endpoints
   - ✅ Diagram validation endpoints
   - ✅ Diagram conversion endpoints
   - 🔄 Conversation endpoints (Pending)

5. **Storage and Persistence**
   - Diagram storage
   - Conversation history
   - User preferences

### Diagram Maintenance

As development proceeds, we will:
1. Update the class diagram to reflect actual implementations
2. Adjust the sequence diagrams to match real interaction flows
3. Refine the user journey based on implemented features
4. Create additional diagrams for specific components as needed

## Consequences

### Positive
- Focusing on the backend first ensures a stable foundation
- Test-driven development reduces defects and guides implementation
- Keeping diagrams updated ensures documentation accuracy
- Virtual environments provide consistency across development environments
- Structured approach reduces integration issues later

### Negative
- Delayed frontend development may extend the timeline for a functional demo
- Regular diagram updates require additional effort
- Test-driven approach may initially slow development velocity

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Ollama integration issues | Implement mock responses for development and testing |
| Complex diagram validation | Start with basic validation and expand incrementally |
| Test coverage gaps | Use coverage tools to identify untested code paths |
| Environment inconsistencies | Provide detailed setup documentation and containerization |
| Outdated diagrams | Schedule regular diagram review sessions |

## Setup Instructions

### Environment Setup

1. **Prerequisites**
   - Python 3.9+ installed
   - Node.js 16+ installed (for later frontend development)
   - Ollama installed and running locally
   - Git

2. **Backend Setup**
   ```bash
   # Clone repository
   git clone [repository-url]
   cd diagram_generator
   
   # Create and activate virtual environment
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Install dev dependencies
   pip install -r requirements-dev.txt
   
   # Run tests to verify setup
   pytest
   ```

3. **Ollama Configuration**
   ```bash
   # Verify Ollama is running
   curl http://localhost:11434/api/version
   
   # List available models
   curl http://localhost:11434/api/tags
   ```

### Development Workflow

1. **Running the Backend**
   ```bash
   # Start the backend server
   uvicorn backend.main:app --reload
   ```

2. **Running Tests**
   ```bash
   # Run all tests
   pytest
   
   # Run tests with coverage
   pytest --cov=backend
   
   # Run specific test modules
   pytest tests/test_ollama_service.py
   ```

3. **Updating Diagrams**
   - After significant backend changes, update the corresponding diagrams in `/docs/diagrams`
   - Use the LLM Diagram Generator itself when operational to update its own diagrams

### Pre-Launch Checklist

Before running the backend:
1. Start Ollama service:
   ```bash
   # Windows (via PowerShell, run as Administrator)
   ollama serve

   # Linux/Mac
   sudo systemctl start ollama
   # or
   ollama serve
   ```
2. Verify Ollama is running and accessible:
   ```bash
   # Windows (PowerShell)
   Invoke-WebRequest -Uri "http://localhost:11434/api/version"
   
   # Linux/Mac
   curl http://localhost:11434/api/version
   ```
3. Initialize required model:
   ```bash
   ollama pull llama3.1:8b
   ```
3. Check the virtual environment is activated
4. Confirm all environment variables are set
5. Validate database connection (if applicable)
