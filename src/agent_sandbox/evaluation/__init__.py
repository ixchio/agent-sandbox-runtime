"""
Evaluation Pipeline
===================

Benchmark runner for measuring agent performance.
"""

from agent_sandbox.evaluation.metrics import MetricsCollector
from agent_sandbox.evaluation.problems import BENCHMARK_PROBLEMS
from agent_sandbox.evaluation.runner import BenchmarkRunner

__all__ = [
    "BenchmarkRunner",
    "MetricsCollector",
    "BENCHMARK_PROBLEMS",
]
