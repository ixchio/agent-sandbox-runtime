"""
Tests for Pydantic Contracts
"""

import pytest
from pydantic import ValidationError

from agent_sandbox.contracts.agent_output import AgentOutput, CritiqueOutput


class TestAgentOutput:
    """Tests for AgentOutput schema."""

    def test_valid_output(self):
        """Test valid output is accepted."""
        output = AgentOutput(
            code="print('hello')",
            dependencies=[],
            reasoning="Simple print statement",
            confidence=0.9,
        )
        assert output.code == "print('hello')"
        assert output.confidence == 0.9

    def test_missing_code_fails(self):
        """Test that missing code raises error."""
        with pytest.raises(ValidationError):
            AgentOutput(
                code="",  # Empty code should fail
                reasoning="test",
            )

    def test_dangerous_code_blocked(self):
        """Test that dangerous patterns are blocked."""
        with pytest.raises(ValidationError) as exc_info:
            AgentOutput(
                code="import os; os.system('rm -rf /')",
                reasoning="Dangerous code",
            )
        # Check that validation error is raised (code is blocked)
        assert "blocked" in str(exc_info.value).lower() or "os.system" in str(exc_info.value)

    def test_eval_blocked(self):
        """Test that eval is blocked."""
        with pytest.raises(ValidationError):
            AgentOutput(
                code="eval(input())",
                reasoning="Using eval",
            )

    def test_dependency_validation(self):
        """Test dependency name validation."""
        output = AgentOutput(
            code="import numpy as np",
            dependencies=["numpy", "pandas>=2.0"],
            reasoning="Using numpy",
        )
        assert "numpy" in output.dependencies

    def test_invalid_dependency_name(self):
        """Test invalid dependency names are rejected."""
        with pytest.raises(ValidationError):
            AgentOutput(
                code="print('hi')",
                dependencies=["123invalid"],  # Can't start with number
                reasoning="test",
            )

    def test_confidence_bounds(self):
        """Test confidence is bounded 0-1."""
        # Valid confidence
        output = AgentOutput(
            code="print(1)",
            reasoning="Testing confidence validation",
            confidence=0.5,
        )
        assert output.confidence == 0.5

        # Invalid confidence
        with pytest.raises(ValidationError):
            AgentOutput(
                code="print(1)",
                reasoning="Testing confidence validation",
                confidence=1.5,  # > 1.0
            )

    def test_incomplete_code_detected(self):
        """Test that incomplete code is detected."""
        with pytest.raises(ValidationError):
            AgentOutput(
                code="def foo():\n    ...",  # Ends with ...
                reasoning="Testing validation",
            )

    @pytest.mark.xfail(reason="Bracket validation not yet implemented")
    def test_unbalanced_brackets(self):
        """Test that unbalanced brackets are detected."""
        with pytest.raises(ValidationError):
            AgentOutput(
                code="print((1 + 2)",  # Missing closing paren
                reasoning="Testing validation",
            )


class TestCritiqueOutput:
    """Tests for CritiqueOutput schema."""

    def test_valid_critique(self):
        """Test valid critique is accepted."""
        critique = CritiqueOutput(
            diagnosis="The function lacks a base case",
            fix_suggestion="Add: if n <= 1: return n",
            should_retry=True,
            confidence=0.8,
        )
        assert critique.should_retry is True

    def test_minimum_length(self):
        """Test minimum length requirements."""
        with pytest.raises(ValidationError):
            CritiqueOutput(
                diagnosis="Bad",  # Too short
                fix_suggestion="Fix it",  # Too short
            )
