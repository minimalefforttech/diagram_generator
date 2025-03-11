# ADR 003: Project Restructuring

## Status
Implemented

## Context
As the project has evolved, we needed to improve the organization of the codebase to enhance maintainability, testability, and follow Python best practices. The initial structure had all Python code directly in the root directory, which could lead to import issues and didn't follow standard Python package conventions.

## Decision

### Project Restructuring

We have reorganized the project structure to follow Python package conventions:

1. **Python Package Structure**: Moved all Python code under a proper package structure:
   - Created a `python/diagram_generator` directory
   - Moved all backend code under `python/diagram_generator/backend`
   - Maintained the existing module structure under the new package

2. **Import Path Updates**: Updated all import statements to use the new package structure:
   - Changed imports from `backend.X` to `diagram_generator.backend.X`
   - Updated all test files to use the new import paths

3. **Test Organization**: Maintained the existing test structure but updated imports:
   - Tests remain in the `tests` directory at the project root
   - Test imports now reference the new package structure

4. **Configuration Updates**: Updated configuration files to reflect the new structure:
   - Modified `pytest.ini` to include the Python path
   - Updated any path references in configuration files

### Package Structure

The new structure follows this pattern:

```
diagram_generator/
├── python/
│   └── diagram_generator/
│       ├── __init__.py
│       └── backend/
│           ├── __init__.py
│           ├── main.py
│           ├── agents/
│           ├── api/
│           ├── core/
│           ├── models/
│           ├── services/
│           ├── storage/
│           └── utils/
├── tests/
│   ├── __init__.py
│   ├── agents/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   ├── storage/
│   └── utils/
├── docs/
├── data/
└── requirements.txt
```

### Technical Improvements

Along with the restructuring, we made several technical improvements:

1. **Pydantic V2 Compatibility**: Updated all Pydantic models to use V2 syntax:
   - Changed validators to use `field_validator` instead of `validator`
   - Updated serialization methods to use `model_dump()` instead of deprecated methods
   - Added proper JSON serialization for datetime objects

2. **Enhanced Resilience Features**:
   - Added jitter support to retry mechanisms
   - Improved circuit breaker implementation
   - Fixed synchronous retry handling

3. **Improved Testing**:
   - Updated mock objects to match the new LangChain interfaces
   - Fixed test assertions to handle whitespace normalization
   - Added comprehensive validation for configuration models

## Consequences

### Positive
- Proper Python package structure improves imports and maintainability
- Better compatibility with modern Python tooling and practices
- Enhanced resilience features improve system stability
- Pydantic V2 compatibility ensures future-proofing

### Negative
- One-time effort to update all import paths
- Potential for temporary import errors during transition
- Need to update documentation to reflect new structure

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Missing import updates | Comprehensive test suite to catch import errors |
| Confusion about new structure | Updated documentation and this ADR |
| Deployment issues | Update deployment scripts to use new paths |

## Implementation Notes

The restructuring was implemented with these steps:

1. Created the new directory structure
2. Moved all Python files to their new locations
3. Updated import statements throughout the codebase
4. Fixed Pydantic models for V2 compatibility
5. Enhanced resilience features
6. Updated tests to work with the new structure
7. Verified all tests pass with the new structure

## Future Considerations

- Consider using a tool like `pyproject.toml` for modern Python packaging
- Evaluate adding type checking with mypy to the CI pipeline
- Consider containerization to simplify deployment with the new structure
