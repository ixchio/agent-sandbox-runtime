"""
Tests for Sandbox Models
"""

import pytest

from agent_sandbox.sandbox.models import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)


class TestExecutionRequest:
    """Tests for ExecutionRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = ExecutionRequest(
            code="print('hello')",
            language="python",
            timeout_seconds=5.0,
        )
        assert request.code == "print('hello')"
        assert request.timeout_seconds == 5.0

    def test_defaults(self):
        """Test default values."""
        request = ExecutionRequest(code="x = 1")
        assert request.language == "python"
        assert request.timeout_seconds == 5.0
        assert request.memory_limit_mb == 256
        assert request.network_enabled is False
        assert request.dependencies == []

    def test_timeout_bounds(self):
        """Test timeout is bounded."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ExecutionRequest(code="x", timeout_seconds=100)  # > 60

        with pytest.raises(ValidationError):
            ExecutionRequest(code="x", timeout_seconds=0.01)  # < 0.1


class TestExecutionResult:
    """Tests for ExecutionResult model."""

    def test_success_result(self):
        """Test successful execution result."""
        result = ExecutionResult(
            stdout="Hello, World!",
            stderr="",
            exit_code=0,
            status=ExecutionStatus.SUCCESS,
            execution_time_ms=100.0,
        )
        assert result.is_success is True
        assert result.has_error is False

    def test_error_result(self):
        """Test error execution result."""
        result = ExecutionResult(
            stdout="",
            stderr="NameError: name 'foo' is not defined",
            exit_code=1,
            status=ExecutionStatus.ERROR,
        )
        assert result.is_success is False
        assert result.has_error is True

    def test_timeout_result(self):
        """Test timeout execution result."""
        result = ExecutionResult(
            stdout="",
            stderr="",
            exit_code=0,
            timed_out=True,
            status=ExecutionStatus.TIMEOUT,
            execution_time_ms=5000.0,
        )
        assert result.is_success is False
        assert result.has_error is True

    def test_error_summary_extraction(self):
        """Test error summary extraction."""
        result = ExecutionResult(
            stderr="Traceback (most recent call last):\n  File...\nValueError: invalid",
            exit_code=1,
        )
        summary = result.get_error_summary()
        assert "Traceback" in summary or "ValueError" in summary

    def test_timeout_error_summary(self):
        """Test timeout error summary."""
        result = ExecutionResult(
            timed_out=True,
            execution_time_ms=5000.0,
        )
        summary = result.get_error_summary()
        assert "timed out" in summary.lower()
