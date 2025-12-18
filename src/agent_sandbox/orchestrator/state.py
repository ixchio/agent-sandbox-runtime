"""
Agent State Schema
==================

Defines the state that flows through the LangGraph workflow.
This is the "memory" of the agent as it executes.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any

from langgraph.graph import add_messages
from pydantic import BaseModel, Field

from agent_sandbox.sandbox.models import ExecutionResult


class HistoryEntry(BaseModel):
    """A single entry in the agent's execution history."""

    attempt: int
    code: str
    result: ExecutionResult | None = None
    critique: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentState(BaseModel):
    """
    State flowing through the LangGraph.

    This captures:
    - The original task
    - Current code solution
    - Execution results
    - Critique feedback
    - Full history for learning
    """

    # Input
    task: str = Field(..., description="The original user task/question")

    # Current solution
    code: str = Field(default="", description="Current Python code solution")
    dependencies: list[str] = Field(default_factory=list, description="Required pip packages")
    reasoning: str = Field(default="", description="Agent's reasoning for the solution")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Agent's confidence in the solution"
    )

    # Execution
    execution_result: ExecutionResult | None = Field(
        default=None, description="Result from sandbox execution"
    )

    # Reflexion
    critique: str | None = Field(default=None, description="Critique from the reviewer")
    should_retry: bool = Field(default=False, description="Whether to retry after critique")

    # Control flow
    attempt: int = Field(default=0, description="Current attempt number")
    max_attempts: int = Field(default=3, description="Maximum retry attempts")

    # History for learning
    history: list[HistoryEntry] = Field(default_factory=list, description="Full execution history")

    # Messages for LangGraph (optional, for chat-based agents)
    messages: Annotated[Sequence[Any], add_messages] = Field(
        default_factory=list, description="Chat messages"
    )

    # Final status
    completed: bool = Field(default=False, description="Whether the task is complete")
    success: bool = Field(default=False, description="Whether the task succeeded")
    final_output: str | None = Field(default=None, description="Final output to return to user")

    def add_to_history(self) -> None:
        """Add current state to history."""
        entry = HistoryEntry(
            attempt=self.attempt,
            code=self.code,
            result=self.execution_result,
            critique=self.critique,
        )
        self.history.append(entry)

    def get_error_context(self) -> str:
        """Get formatted error context for the LLM."""
        if not self.execution_result:
            return ""

        result = self.execution_result
        context_parts = []

        if result.stderr:
            context_parts.append(f"Error Output:\n```\n{result.stderr}\n```")

        if result.timed_out:
            context_parts.append(f"⚠️ Execution timed out after {result.execution_time_ms:.0f}ms")

        if self.critique:
            context_parts.append(f"Reviewer Feedback:\n{self.critique}")

        return "\n\n".join(context_parts)

    def can_retry(self) -> bool:
        """Check if retry is possible."""
        return self.attempt < self.max_attempts and self.should_retry


class AgentStateDict(dict):
    """
    Dictionary-based state for LangGraph compatibility.

    LangGraph uses TypedDict, so we provide conversion utilities.
    """

    @classmethod
    def from_model(cls, state: AgentState) -> "AgentStateDict":
        """Convert Pydantic model to dict."""
        return cls(state.model_dump())

    def to_model(self) -> AgentState:
        """Convert dict back to Pydantic model."""
        return AgentState(**self)
