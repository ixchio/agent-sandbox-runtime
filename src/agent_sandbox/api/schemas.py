"""
API Request/Response Schemas
============================

Pydantic models for API contracts.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of an execution job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecuteRequest(BaseModel):
    """Request to execute an agent task."""

    task: str = Field(
        ...,
        description="Task description for the agent",
        min_length=1,
        max_length=10000,
        examples=["Write a Python function to calculate the Fibonacci sequence"],
    )

    max_attempts: int = Field(
        default=3, ge=1, le=10, description="Maximum retry attempts for self-correction"
    )

    timeout_seconds: float = Field(
        default=5.0, ge=1.0, le=60.0, description="Timeout for each code execution"
    )

    stream: bool = Field(default=False, description="Enable streaming responses")


class ExecutionStep(BaseModel):
    """A single step in the execution history."""

    step: str
    timestamp: datetime
    data: dict[str, Any] = Field(default_factory=dict)


class ExecuteResponse(BaseModel):
    """Response from agent execution."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")

    # Result
    success: bool = Field(default=False, description="Whether execution succeeded")
    output: str | None = Field(None, description="Final output from execution")

    # Generated code
    code: str | None = Field(None, description="Generated Python code")
    dependencies: list[str] = Field(default_factory=list, description="Required packages")
    reasoning: str | None = Field(None, description="Agent's reasoning")

    # Execution details
    attempts: int = Field(default=0, description="Number of attempts made")
    execution_time_ms: float = Field(default=0, description="Total execution time")

    # Error info
    error: str | None = Field(None, description="Error message if failed")

    # History
    history: list[ExecutionStep] = Field(default_factory=list, description="Execution history")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    service: str = "agent-sandbox-runtime"
    sandbox_ready: bool = True
    uptime_seconds: float = 0


class BenchmarkRequest(BaseModel):
    """Request to run benchmarks."""

    suite: str = Field(default="quick", description="Benchmark suite to run (quick, full, custom)")

    max_problems: int = Field(
        default=10, ge=1, le=100, description="Maximum number of problems to run"
    )


class BenchmarkResponse(BaseModel):
    """Benchmark results response."""

    suite: str
    total: int
    passed: int
    failed: int
    success_rate: float
    average_attempts: float
    average_time_ms: float
    results: list[dict[str, Any]] = Field(default_factory=list)


class StatsResponse(BaseModel):
    """System statistics response."""

    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_attempts: float = 0.0
    average_execution_time_ms: float = 0.0
    sandbox_stats: dict[str, Any] = Field(default_factory=dict)
