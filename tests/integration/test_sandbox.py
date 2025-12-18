"""
Integration Tests for Sandbox Manager

These tests require Docker to be running.
"""

import pytest

from agent_sandbox.sandbox.manager import SandboxManager
from agent_sandbox.sandbox.models import ExecutionRequest, ExecutionStatus
from agent_sandbox.config import Settings


@pytest.fixture
async def sandbox_manager():
    """Create and initialize a sandbox manager."""
    settings = Settings(
        groq_api_key="test-key",  # Not used for sandbox tests
        sandbox_timeout_seconds=5.0,
        sandbox_memory_limit_mb=128,
    )
    manager = SandboxManager(settings)
    await manager.initialize()
    yield manager
    await manager.cleanup()


@pytest.mark.integration
@pytest.mark.slow
class TestSandboxManager:
    """Integration tests for SandboxManager."""

    async def test_simple_execution(self, sandbox_manager):
        """Test simple code execution."""
        request = ExecutionRequest(
            code="print('Hello, Sandbox!')",
        )

        result = await sandbox_manager.execute(request)

        assert result.status == ExecutionStatus.SUCCESS
        assert result.exit_code == 0
        assert "Hello, Sandbox!" in result.stdout

    async def test_math_execution(self, sandbox_manager):
        """Test math operations."""
        request = ExecutionRequest(
            code="print(2 + 2)",
        )

        result = await sandbox_manager.execute(request)

        assert result.exit_code == 0
        assert "4" in result.stdout

    async def test_error_captured(self, sandbox_manager):
        """Test that errors are captured."""
        request = ExecutionRequest(
            code="raise ValueError('Test error')",
        )

        result = await sandbox_manager.execute(request)

        assert result.exit_code != 0
        assert "ValueError" in result.stderr

    async def test_syntax_error(self, sandbox_manager):
        """Test syntax error handling."""
        request = ExecutionRequest(
            code="def broken(",
        )

        result = await sandbox_manager.execute(request)

        assert result.exit_code != 0
        assert "SyntaxError" in result.stderr

    async def test_timeout(self, sandbox_manager):
        """Test that timeout works."""
        request = ExecutionRequest(
            code="import time; time.sleep(10)",
            timeout_seconds=1.0,
        )

        result = await sandbox_manager.execute(request)

        assert result.timed_out is True
        assert result.status == ExecutionStatus.TIMEOUT

    async def test_import_stdlib(self, sandbox_manager):
        """Test importing standard library."""
        request = ExecutionRequest(
            code="import json; print(json.dumps({'a': 1}))",
        )

        result = await sandbox_manager.execute(request)

        assert result.exit_code == 0
        assert '{"a": 1}' in result.stdout

    async def test_multiline_code(self, sandbox_manager):
        """Test multiline code execution."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""
        request = ExecutionRequest(code=code)

        result = await sandbox_manager.execute(request)

        assert result.exit_code == 0
        assert "55" in result.stdout
