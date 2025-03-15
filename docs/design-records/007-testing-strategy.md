# ADR 007: Testing Strategy Implementation

## Status
Proposed

## Context
We need to implement a comprehensive testing strategy to ensure system reliability and maintain at least 50% code coverage. Key considerations:

1. Current lack of systematic testing approach
2. Need for consistent coverage across components
3. Complex interactions between frontend and backend
4. Specific testing needs for LLM-based systems
5. Integration with CI/CD pipeline

## Decision

### 1. Coverage Requirements

Establish minimum coverage requirements:

- Overall project: 50% minimum coverage
- Critical paths: 75% minimum coverage
- Core modules priority list:
  1. Diagram generation and validation (backend)
  2. RAG integration (backend)
  3. API endpoints (backend)
  4. Configuration management (frontend)
  5. Diagram rendering (frontend)

### 2. Backend Testing Strategy

#### a. Unit Tests

Focus areas:
```python
# Example test structure
python/diagram_generator/tests/
├── agents/
│   ├── test_diagram_agent.py
│   └── test_rag_provider.py
├── api/
│   ├── test_diagrams.py
│   └── test_ollama.py
├── core/
│   └── test_diagram_generator.py
├── utils/
│   ├── test_diagram_validator.py
│   └── test_rag.py
└── conftest.py
```

Testing approach:
```python
# Example test case
def test_diagram_generation():
    agent = DiagramAgent()
    result = await agent.generate_diagram(
        description="Test diagram",
        diagram_type="mermaid"
    )
    assert result.code is not None
    assert result.valid
    assert "mermaid" in result.code.lower()
```

#### b. Integration Tests

Key integration points:
1. Ollama API interaction
2. RAG with file system
3. PlantUML rendering
4. Storage system

```python
# Example integration test
@pytest.mark.integration
async def test_rag_integration():
    rag_provider = RAGProvider(config=test_config)
    await rag_provider.load_docs_from_directory("test_data/")
    context = await rag_provider.get_relevant_context("test query")
    assert context is not None
    assert len(context.documents) > 0
```

#### c. Mocking Strategy

Implement mocks for:
- Ollama API responses
- File system operations
- Database interactions

```python
# Example mock
@pytest.fixture
def mock_ollama():
    with patch("diagram_generator.services.ollama.OllamaAPI") as mock:
        mock.generate.return_value = {
            "response": "test diagram code"
        }
        yield mock
```

### 3. Frontend Testing Strategy

#### a. Component Tests

Priority components:
1. ConfigurationScreen
2. DiagramPanel
3. CodeEditor
4. RAGConfig
5. ModelSelector

```typescript
// Example component test
describe('ConfigurationScreen', () => {
  it('validates RAG directory input', () => {
    const { getByLabelText, getByText } = render(<ConfigurationScreen />);
    const input = getByLabelText('Reference Directory');
    fireEvent.change(input, { target: { value: 'invalid/path' } });
    expect(getByText('Directory not found')).toBeInTheDocument();
  });
});
```

#### b. Integration Tests

Key frontend integrations:
1. API client integration
2. Diagram rendering
3. Theme system
4. Local storage

```typescript
// Example integration test
describe('DiagramGeneration', () => {
  it('generates and renders diagram', async () => {
    const { getByText, findByTestId } = render(<DiagramWorkspace />);
    fireEvent.click(getByText('Generate'));
    const diagram = await findByTestId('diagram-view');
    expect(diagram).toBeInTheDocument();
  });
});
```

### 4. Test Automation

Implement in CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      
      # Backend tests
      - name: Run Python tests
        run: |
          pip install -r requirements.txt
          pytest --cov=diagram_generator
          
      # Frontend tests
      - name: Run Frontend tests
        run: |
          cd frontend
          npm install
          npm test -- --coverage
          
      # Coverage report
      - name: Check coverage
        run: |
          python scripts/check_coverage.py --min-coverage 50
```

### 5. Test Data Management

Create standardized test data:

```
tests/data/
├── diagrams/
│   ├── mermaid_samples/
│   └── plantuml_samples/
├── docs/
│   └── rag_samples/
└── responses/
    └── ollama_samples/
```

## Consequences

### Positive
- Consistent test coverage
- Early bug detection
- Improved development confidence
- Clear testing standards
- Automated validation

### Negative
- Initial development slowdown
- Maintenance overhead
- Complex test environment setup
- Additional CI/CD time

### Mitigation
- Focused testing on critical paths
- Reusable test utilities
- Clear testing documentation
- Optimized test execution

## Implementation Plan

### Phase 1: Framework Setup
1. Set up testing frameworks
2. Create initial test structure
3. Implement basic mocks
4. Configure coverage reporting

### Phase 2: Backend Tests
1. Implement core unit tests
2. Add integration tests
3. Create mock data
4. Validate coverage

### Phase 3: Frontend Tests
1. Add component tests
2. Implement integration tests
3. Set up E2E testing
4. Verify coverage

### Phase 4: Automation
1. Configure CI/CD integration
2. Add coverage checks
3. Implement test reporting
4. Create documentation

## Success Metrics

1. Coverage Goals:
   - 50% overall coverage
   - 75% coverage for critical paths
   - 0% critical paths without tests

2. Test Quality:
   - All tests documented
   - No flaky tests
   - Fast execution (<5 minutes)
   - Clear failure messages

3. Maintenance:
   - Tests updated with code changes
   - Regular coverage reviews
   - Test documentation current

## References

1. ADR-001: Project Outline
2. ADR-003: Architecture Simplification
3. ADR-006: Build Process and Deployment
4. Testing Best Practices Guide
5. Coverage Reports (to be generated)
