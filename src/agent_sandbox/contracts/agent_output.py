"""Agent output contracts - Pydantic schemas for LLM outputs."""

import re

from pydantic import BaseModel, Field, field_validator, model_validator


class AgentOutput(BaseModel):
    """Code generation output schema."""

    code: str = Field(..., min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    reasoning: str = Field(..., min_length=5)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

    @field_validator("code")
    @classmethod
    def check_safety(cls, v: str) -> str:
        """Block dangerous patterns."""
        blocked = [
            (r"\bos\.system\b", "os.system"),
            (r"\bsubprocess\.", "subprocess"),
            (r"\beval\s*\(", "eval()"),
            (r"\bexec\s*\(", "exec()"),
            (r"\b__import__\s*\(", "__import__"),
            (r"\brmtree\b", "rmtree"),
        ]
        for pat, name in blocked:
            if re.search(pat, v):
                raise ValueError(f"Blocked: {name}")
        return v

    @field_validator("dependencies")
    @classmethod
    def validate_deps(cls, v: list[str]) -> list[str]:
        """Normalize dependencies."""
        result = []
        for dep in v:
            name = re.split(r"[<>=!]", dep)[0].strip()
            if name and re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
                result.append(dep.strip())
        return result

    @model_validator(mode="after")
    def check_completeness(self) -> "AgentOutput":
        """Ensure code isn't truncated."""
        if self.code.strip().endswith("..."):
            raise ValueError("Code incomplete")
        return self


class CritiqueOutput(BaseModel):
    """Critic output schema."""

    diagnosis: str = Field(..., min_length=5)
    fix_suggestion: str = Field(..., min_length=5)
    should_retry: bool = True
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    error_category: str | None = None


class BenchmarkResult(BaseModel):
    """Single benchmark result."""

    test_id: str
    test_name: str
    passed: bool
    attempts: int
    execution_time_ms: float
    error_message: str | None = None
    code_generated: str | None = None
    stdout: str | None = None


class BenchmarkSuiteResult(BaseModel):
    """Benchmark suite results."""

    suite_name: str
    total_tests: int
    passed: int
    failed: int
    success_rate: float
    average_attempts: float
    average_execution_time_ms: float
    results: list[BenchmarkResult]

    @property
    def improvement_over_baseline(self) -> float:
        """Improvement vs no-reflexion (60% baseline)."""
        return (self.success_rate - 0.60) / 0.60 * 100
