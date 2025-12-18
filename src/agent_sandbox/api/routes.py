"""
API Routes
==========

FastAPI router with all HTTP endpoints.
"""

import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, HTTPException, Request, status

from agent_sandbox.api.schemas import (
    BenchmarkRequest,
    BenchmarkResponse,
    ExecuteRequest,
    ExecuteResponse,
    HealthResponse,
    JobStatus,
    StatsResponse,
)
from agent_sandbox.orchestrator.graph import AgentGraph
from agent_sandbox.sandbox.manager import SandboxManager

logger = structlog.get_logger()

router = APIRouter(tags=["agent"])


# In-memory job storage (replace with Redis in production)
_jobs: dict[str, ExecuteResponse] = {}
_stats = {
    "total_executions": 0,
    "successful": 0,
    "failed": 0,
    "total_attempts": 0,
    "total_time_ms": 0,
}


def get_sandbox_manager(request: Request) -> SandboxManager:
    """Get sandbox manager from app state."""
    return request.app.state.sandbox_manager


@router.post(
    "/execute",
    response_model=ExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute an agent task",
    description="""
    Submit a task for the agent to solve.

    The agent will:
    1. Generate Python code using Groq LLM
    2. Execute in a Docker sandbox
    3. Self-correct on errors (up to max_attempts)
    4. Return the result

    This is a synchronous endpoint - it waits for completion.
    For streaming, set `stream: true` and use the WebSocket endpoint.
    """,
)
async def execute_task(
    request: Request,
    body: ExecuteRequest,
) -> ExecuteResponse:
    """Execute an agent task synchronously."""

    job_id = str(uuid.uuid4())[:8]
    sandbox_manager = get_sandbox_manager(request)

    logger.info(
        "Received execution request",
        job_id=job_id,
        task=body.task[:100],
    )

    # Create initial response
    response = ExecuteResponse(
        job_id=job_id,
        status=JobStatus.RUNNING,
        created_at=datetime.now(UTC),
    )
    _jobs[job_id] = response

    try:
        # Create agent graph
        agent = AgentGraph(sandbox_manager)

        # Run the agent
        start_time = datetime.now(UTC)
        result = await agent.run(
            task=body.task,
            max_attempts=body.max_attempts,
        )
        end_time = datetime.now(UTC)

        # Calculate execution time
        execution_time_ms = (end_time - start_time).total_seconds() * 1000

        # Update response
        response.status = JobStatus.COMPLETED
        response.success = result.get("success", False)
        response.output = result.get("final_output", "")
        response.code = result.get("code", "")
        response.dependencies = result.get("dependencies", [])
        response.reasoning = result.get("reasoning", "")
        response.attempts = result.get("attempt", 1)
        response.execution_time_ms = execution_time_ms
        response.completed_at = end_time

        if not response.success:
            response.error = result.get("final_output", "Execution failed")

        # Update stats
        _stats["total_executions"] += 1
        _stats["total_attempts"] += response.attempts
        _stats["total_time_ms"] += execution_time_ms
        if response.success:
            _stats["successful"] += 1
        else:
            _stats["failed"] += 1

        logger.info(
            "Execution completed",
            job_id=job_id,
            success=response.success,
            attempts=response.attempts,
            time_ms=execution_time_ms,
        )

    except Exception as e:
        logger.error(
            "Execution failed",
            job_id=job_id,
            error=str(e),
        )
        response.status = JobStatus.FAILED
        response.error = str(e)
        response.completed_at = datetime.now(UTC)
        _stats["total_executions"] += 1
        _stats["failed"] += 1

    _jobs[job_id] = response
    return response


@router.get(
    "/jobs/{job_id}",
    response_model=ExecuteResponse,
    summary="Get job status",
)
async def get_job(job_id: str) -> ExecuteResponse:
    """Get the status of an execution job."""

    if job_id not in _jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return _jobs[job_id]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health_check(request: Request) -> HealthResponse:
    """Check service health."""

    sandbox_manager = get_sandbox_manager(request)
    sandbox_stats = await sandbox_manager.get_stats()

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        sandbox_ready=sandbox_stats.get("initialized", False),
    )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get execution statistics",
)
async def get_stats(request: Request) -> StatsResponse:
    """Get aggregate execution statistics."""

    sandbox_manager = get_sandbox_manager(request)
    sandbox_stats = await sandbox_manager.get_stats()

    total = _stats["total_executions"]

    return StatsResponse(
        total_executions=total,
        successful_executions=_stats["successful"],
        failed_executions=_stats["failed"],
        average_attempts=_stats["total_attempts"] / max(total, 1),
        average_execution_time_ms=_stats["total_time_ms"] / max(total, 1),
        sandbox_stats=sandbox_stats,
    )


@router.post(
    "/benchmark",
    response_model=BenchmarkResponse,
    summary="Run benchmarks",
    description="Run the agent against a benchmark suite to measure performance.",
)
async def run_benchmark(
    request: Request,
    body: BenchmarkRequest,
) -> BenchmarkResponse:
    """Run benchmark suite."""

    # Import here to avoid circular dependency
    from agent_sandbox.evaluation.runner import BenchmarkRunner

    sandbox_manager = get_sandbox_manager(request)
    runner = BenchmarkRunner(sandbox_manager)

    logger.info(
        "Starting benchmark",
        suite=body.suite,
        max_problems=body.max_problems,
    )

    results = await runner.run_suite(
        suite_name=body.suite,
        max_problems=body.max_problems,
    )

    return BenchmarkResponse(
        suite=body.suite,
        total=results.total_tests,
        passed=results.passed,
        failed=results.failed,
        success_rate=results.success_rate,
        average_attempts=results.average_attempts,
        average_time_ms=results.average_execution_time_ms,
        results=[r.model_dump() for r in results.results],
    )


@router.delete(
    "/jobs",
    summary="Clear all jobs",
    description="Clear the in-memory job storage (development only).",
)
async def clear_jobs() -> dict:
    """Clear all stored jobs."""
    count = len(_jobs)
    _jobs.clear()
    return {"cleared": count}
