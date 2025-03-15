"""Global test configuration and fixtures."""

import pytest
from pathlib import Path
from diagram_generator.backend.models.configs import (
    AgentConfig,
    DiagramGenerationOptions,
    DiagramRAGConfig,
    RetrySettings,
    CircuitBreakerSettings
)

@pytest.fixture
def agent_config():
    """Basic agent configuration with default model."""
    return AgentConfig(
        enabled=True,
        model_name="llama3.1:8b",
        temperature=0.2,
        max_iterations=3,
        system_prompt=None,
        retry=RetrySettings(),
        circuit_breaker=CircuitBreakerSettings()
    )

@pytest.fixture
def generation_options(agent_config):
    """Generation options with default settings."""
    return DiagramGenerationOptions(
        agent=agent_config,
        rag=DiagramRAGConfig(
            enabled=False,
            api_doc_dir="",
            similarity_threshold=0.7
        )
    )

@pytest.fixture
def test_description():
    """Sample diagram description for tests."""
    return "Create a sequence diagram showing user login flow"

@pytest.fixture
def test_code_dir(tmp_path):
    """Create a temporary directory with sample code files."""
    dir_path = tmp_path / "test_code"
    dir_path.mkdir()
    
    # Create a sample Python file
    sample_py = dir_path / "sample.py"
    sample_py.write_text("""
class User:
    def __init__(self, username):
        self.username = username
    
    def login(self):
        return f"{self.username} logged in"
""")
    
    # Create a sample TypeScript file
    sample_ts = dir_path / "auth.ts"
    sample_ts.write_text("""
export class AuthService {
    async validateUser(username: string): Promise<boolean> {
        return true;
    }
}
""")
    
    return dir_path
