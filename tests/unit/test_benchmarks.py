"""
Tests for Benchmark Problems
"""

import pytest

from agent_sandbox.evaluation.problems import (
    BENCHMARK_PROBLEMS,
    PROBLEM_SUITES,
    get_suite,
    BenchmarkProblem,
)


class TestBenchmarkProblems:
    """Tests for benchmark problem definitions."""

    def test_problems_exist(self):
        """Test that problems are defined."""
        assert len(BENCHMARK_PROBLEMS) > 0

    def test_all_problems_have_required_fields(self):
        """Test all problems have required fields."""
        for problem in BENCHMARK_PROBLEMS:
            assert problem.id, f"Problem missing id"
            assert problem.name, f"Problem {problem.id} missing name"
            assert problem.task, f"Problem {problem.id} missing task"
            assert problem.difficulty in ["easy", "medium", "hard"]

    def test_all_problems_have_expected_output(self):
        """Test all problems have some form of expected output."""
        for problem in BENCHMARK_PROBLEMS:
            has_expected = problem.expected_output or problem.expected_contains or problem.test_code
            assert has_expected, f"Problem {problem.id} has no expected output"

    def test_unique_problem_ids(self):
        """Test that all problem IDs are unique."""
        ids = [p.id for p in BENCHMARK_PROBLEMS]
        assert len(ids) == len(set(ids)), "Duplicate problem IDs found"

    def test_suites_exist(self):
        """Test that problem suites are defined."""
        assert "quick" in PROBLEM_SUITES
        assert "full" in PROBLEM_SUITES
        assert "algorithms" in PROBLEM_SUITES

    def test_get_suite(self):
        """Test get_suite function."""
        quick = get_suite("quick")
        assert len(quick) > 0
        assert len(quick) <= 10  # Quick should be small

        full = get_suite("full")
        assert len(full) == len(BENCHMARK_PROBLEMS)

    def test_get_unknown_suite_returns_quick(self):
        """Test that unknown suite returns quick."""
        result = get_suite("nonexistent")
        assert result == PROBLEM_SUITES["quick"]

    def test_problem_model_validation(self):
        """Test BenchmarkProblem model validation."""
        problem = BenchmarkProblem(
            id="test-001",
            name="Test Problem",
            task="Write hello world",
            expected_contains=["hello"],
            difficulty="easy",
            category="test",
        )
        assert problem.timeout_seconds == 5.0  # Default
