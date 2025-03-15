# ADR 003: Simplifying Architecture and Improving Development Experience

## Status
Proposed

## Context
We have identified several issues that need to be addressed to improve the development experience and system reliability:

1. LangChain integration is causing compatibility issues that complicate development
2. The current development workflow requires unnecessary pip package installation steps
3. The diagram generation system is not functioning properly and defaults to fallbacks
4. Error handling needs improvement to better support developer debugging

## Decision

We will make the following architectural changes to address these issues:

### 1. Migration from LangChain to Pure Pydantic

We will remove LangChain dependency and switch to a simpler architecture:

- Replace LangChain components with direct Pydantic models
- Implement direct Ollama API integration without middleware
- Simplify the agent system to use basic Python classes

Benefits:
- Reduced complexity in the codebase
- Better control over API interactions
- Fewer dependency conflicts
- More straightforward testing and maintenance
- Faster development iterations

Drawbacks:
- Need to reimplement some functionality that LangChain provided
- Temporary development slowdown during migration
- Need to update existing tests

### 2. Development Workflow Enhancement

Update the runner system to work without requiring pip package installation:

- Add Python path configuration in the runner
- Automatically detect and set PYTHONPATH if not configured
- Maintain pip package support for production deployments
- Document both development and production setup processes

Benefits:
- Faster local development setup
- Reduced friction during development
- Clearer separation between development and production environments

Implementation:
```python
# Runner will include logic like:
if 'PYTHONPATH' not in os.environ:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python_path = os.path.join(project_root, 'python')
    os.environ['PYTHONPATH'] = python_path
```

### 3. Diagram Generation Improvements

Overhaul the diagram generation system:

- Remove all fallback mechanisms
- Implement proper error handling and logging
- Add comprehensive logging for debugging
- Expose errors through VSCode output panel

The new diagram generation flow will:
1. Parse user input
2. Generate diagram structure
3. Validate syntax
4. Return either valid diagram or detailed error information

### 4. Enhanced Error Handling

Implement a new error handling system focused on developer visibility:

- Replace generic fallbacks with specific error types
- Add VSCode output panel integration
- Log full error context including:
  - Error type and message
  - Stack trace
  - Input that caused the error
  - System state at time of error
- Display errors in UI for immediate developer awareness

## Implementation Plan

### Phase 1: Core Architecture Updates
1. Remove LangChain dependencies
2. Implement Pydantic models for data validation
3. Create direct Ollama integration
4. Update runner with Python path handling

### Phase 2: Error Handling & Logging
1. Set up VSCode output panel integration
2. Implement error logging system
3. Create error type hierarchy
4. Add UI error display components

### Phase 3: Diagram Generation
1. Remove fallback mechanisms
2. Implement new generation pipeline
3. Add validation system
4. Update tests for new system

### Phase 4: Testing & Documentation
1. Update all test suites
2. Add developer documentation
3. Update setup instructions
4. Document common error scenarios

## Consequences

### Positive
- Simpler, more maintainable codebase
- Better development experience
- More reliable diagram generation
- Better visibility into errors
- Faster local development setup

### Negative
- Initial development time to implement changes
- Need to rewrite some existing functionality
- Temporary disruption during migration

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing functionality | Comprehensive test coverage before/after changes |
| Migration complexity | Phased approach with validation at each step |
| Knowledge loss from LangChain removal | Document all custom implementations |
| Development delays | Focus on critical paths first |

## Success Metrics

We will measure the success of these changes by:

1. Development Environment
   - Time to set up new development environment
   - Number of setup-related issues reported

2. Error Handling
   - Time to diagnose issues
   - Quality of error information
   - Developer satisfaction with debugging process

3. Code Quality
   - Test coverage
   - Number of dependencies
   - Code complexity metrics

4. System Reliability
   - Number of fallback activations (should be zero)
   - Successful diagram generation rate
   - System uptime and performance

## Follow-up

After implementation, we should:

1. Monitor system performance and reliability
2. Gather developer feedback on new workflow
3. Document any common issues and solutions
4. Consider additional improvements based on usage patterns
5. Regular review of error logs to identify patterns
