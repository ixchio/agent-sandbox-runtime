"""
Sandbox Data Models
===================

Pydantic models for execution requests and results.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Status of code execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExecutionRequest(BaseModel):
    """Request to execute code in sandbox."""

    code: str = Field(
        ...,
        description="Python code to execute",
        min_length=1,
        max_length=100_000,
    )
    language: str = Field(default="python", description="Programming language")
    timeout_seconds: float = Field(
        default=5.0, ge=0.1, le=60.0, description="Maximum execution time"
    )
    memory_limit_mb: int = Field(default=256, ge=32, le=2048, description="Memory limit in MB")
    network_enabled: bool = Field(default=False, description="Allow network access")
    dependencies: list[str] = Field(default_factory=list, description="Pip packages to install")


class ExecutionResult(BaseModel):
    """Result from sandbox code execution."""

    # Execution output
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    exit_code: int = Field(default=0, description="Process exit code")

    # Metadata
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    execution_time_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    memory_used_mb: float = Field(default=0.0, description="Peak memory usage in MB")

    # Flags
    timed_out: bool = Field(default=False)
    killed: bool = Field(default=False)

    # Timestamps
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Container info
    container_id: str | None = None

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.exit_code == 0 and not self.timed_out and not self.killed

    @property
    def has_error(self) -> bool:
        """Check if execution had errors."""
        return self.exit_code != 0 or bool(self.stderr) or self.timed_out

    def get_error_summary(self) -> str:
        """Get a summary of the error for the LLM."""
        if self.timed_out:
            return f"Execution timed out after {self.execution_time_ms:.0f}ms"
        if self.stderr:
            # Extract the most relevant error line
            lines = self.stderr.strip().split("\n")
            # Find traceback error
            for i, line in enumerate(lines):
                if line.startswith(("Error:", "Exception:", "Traceback")):
                    return "\n".join(lines[i:])
            return self.stderr[-1000:]  # Last 1000 chars
        if self.exit_code != 0:
            return f"Process exited with code {self.exit_code}"
        return ""
