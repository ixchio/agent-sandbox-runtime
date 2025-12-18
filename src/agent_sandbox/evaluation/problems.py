"""
Benchmark Problems
==================

Collection of coding problems for evaluating agent performance.

Categories:
1. Basic Algorithms - Classic CS problems
2. Error Recovery - Problems with common pitfalls
3. Dependency Management - Package import scenarios
4. Edge Cases - Tricky scenarios

Each problem has:
- task: Description for the agent
- test_code: Python code to verify the result
- expected_output: Expected stdout (partial match)
- difficulty: easy, medium, hard
- category: Problem category
"""

from typing import Literal

from pydantic import BaseModel, Field


class BenchmarkProblem(BaseModel):
    """A single benchmark problem."""

    id: str
    name: str
    task: str
    test_code: str | None = None
    expected_output: str | None = None
    expected_contains: list[str] = Field(default_factory=list)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    category: str = "general"
    timeout_seconds: float = 5.0


# =============================================================================
# BASIC ALGORITHM PROBLEMS
# =============================================================================

BASIC_ALGORITHMS = [
    BenchmarkProblem(
        id="fib-001",
        name="Fibonacci Sequence",
        task="Write a Python function to calculate the nth Fibonacci number and print the 10th Fibonacci number.",
        expected_contains=["55"],
        difficulty="easy",
        category="algorithms",
    ),
    BenchmarkProblem(
        id="prime-001",
        name="Prime Numbers",
        task="Write a Python function to check if a number is prime, then print all prime numbers between 1 and 30.",
        expected_contains=["2", "3", "5", "7", "11", "13", "17", "19", "23", "29"],
        difficulty="easy",
        category="algorithms",
    ),
    BenchmarkProblem(
        id="factorial-001",
        name="Factorial",
        task="Write a Python function to calculate factorial and print the factorial of 10.",
        expected_contains=["3628800"],
        difficulty="easy",
        category="algorithms",
    ),
    BenchmarkProblem(
        id="palindrome-001",
        name="Palindrome Check",
        task="Write a function to check if a string is a palindrome. Test with 'racecar' and 'hello', printing True/False for each.",
        expected_contains=["True", "False"],
        difficulty="easy",
        category="algorithms",
    ),
    BenchmarkProblem(
        id="sort-001",
        name="Custom Sorting",
        task="Implement bubble sort and use it to sort [64, 34, 25, 12, 22, 11, 90]. Print the sorted list.",
        expected_contains=["11", "12", "22", "25", "34", "64", "90"],
        difficulty="medium",
        category="algorithms",
    ),
    BenchmarkProblem(
        id="binary-search-001",
        name="Binary Search",
        task="Implement binary search. Search for 23 in [1, 3, 5, 7, 11, 13, 17, 19, 23, 29]. Print the index.",
        expected_contains=["8"],
        difficulty="medium",
        category="algorithms",
    ),
    BenchmarkProblem(
        id="gcd-001",
        name="GCD Calculation",
        task="Write a function to find the GCD of two numbers using Euclidean algorithm. Print GCD of 48 and 18.",
        expected_contains=["6"],
        difficulty="easy",
        category="algorithms",
    ),
    BenchmarkProblem(
        id="reverse-001",
        name="Reverse String",
        task="Write a function to reverse a string without using slicing or built-in reverse. Reverse 'hello world' and print it.",
        expected_contains=["dlrow olleh"],
        difficulty="easy",
        category="algorithms",
    ),
    BenchmarkProblem(
        id="anagram-001",
        name="Anagram Check",
        task="Write a function to check if two strings are anagrams. Check 'listen' and 'silent', then 'hello' and 'world'. Print True/False for each.",
        expected_contains=["True", "False"],
        difficulty="medium",
        category="algorithms",
    ),
    BenchmarkProblem(
        id="merge-sort-001",
        name="Merge Sort",
        task="Implement merge sort and sort [38, 27, 43, 3, 9, 82, 10]. Print the sorted list.",
        expected_contains=["3", "9", "10", "27", "38", "43", "82"],
        difficulty="hard",
        category="algorithms",
    ),
]

# =============================================================================
# ERROR RECOVERY PROBLEMS (Test reflexion)
# =============================================================================

ERROR_RECOVERY = [
    BenchmarkProblem(
        id="typo-001",
        name="Import Typo Recovery",
        task="Use the 'math' module to calculate and print the square root of 144. (Hint: The function is sqrt, not squareroot)",
        expected_contains=["12"],
        difficulty="easy",
        category="error_recovery",
    ),
    BenchmarkProblem(
        id="edge-001",
        name="Division Edge Case",
        task="Write a safe division function that handles division by zero. Print 10/2, 10/0, and 15/3.",
        expected_contains=["5"],
        difficulty="medium",
        category="error_recovery",
    ),
    BenchmarkProblem(
        id="index-001",
        name="Index Error Recovery",
        task="Create a list [1,2,3] and safely access index 5 (which doesn't exist). Print 'Index out of bounds' if error, otherwise print the value.",
        expected_contains=["out of bounds"],
        difficulty="easy",
        category="error_recovery",
    ),
    BenchmarkProblem(
        id="type-001",
        name="Type Error Recovery",
        task="Write a function that adds two numbers but handles the case where inputs might be strings. Test with add(5, 3) and add('5', '3'). Print results.",
        expected_contains=["8"],
        difficulty="medium",
        category="error_recovery",
    ),
    BenchmarkProblem(
        id="file-001",
        name="File Not Found Recovery",
        task="Try to open a file called 'nonexistent.txt'. Handle the FileNotFoundError gracefully and print 'File not found'.",
        expected_contains=["not found"],
        difficulty="easy",
        category="error_recovery",
    ),
]

# =============================================================================
# DATA MANIPULATION PROBLEMS
# =============================================================================

DATA_MANIPULATION = [
    BenchmarkProblem(
        id="json-001",
        name="JSON Parsing",
        task='Parse this JSON string and print the name: \'{"name": "Alice", "age": 30}\'',
        expected_contains=["Alice"],
        difficulty="easy",
        category="data",
    ),
    BenchmarkProblem(
        id="csv-001",
        name="CSV Processing",
        task="""Create a simple CSV-like data structure:
name,age,city
Alice,30,NYC
Bob,25,LA
Charlie,35,Chicago

Parse it and print just the names, one per line.""",
        expected_contains=["Alice", "Bob", "Charlie"],
        difficulty="medium",
        category="data",
    ),
    BenchmarkProblem(
        id="dict-001",
        name="Dictionary Operations",
        task="Create a dictionary mapping names to ages: Alice=30, Bob=25, Charlie=35. Find and print the oldest person's name.",
        expected_contains=["Charlie"],
        difficulty="easy",
        category="data",
    ),
    BenchmarkProblem(
        id="list-comp-001",
        name="List Comprehension",
        task="Use list comprehension to get squares of even numbers from 1-20. Print the result.",
        expected_contains=["4", "16", "36", "64", "100", "144", "196", "256", "324", "400"],
        difficulty="medium",
        category="data",
    ),
    BenchmarkProblem(
        id="filter-001",
        name="Filter and Map",
        task="Given numbers [1,2,3,4,5,6,7,8,9,10], filter evens and double them. Print the result.",
        expected_contains=["4", "8", "12", "16", "20"],
        difficulty="medium",
        category="data",
    ),
]

# =============================================================================
# MATH/NUMERIC PROBLEMS
# =============================================================================

MATH_PROBLEMS = [
    BenchmarkProblem(
        id="stats-001",
        name="Basic Statistics",
        task="Calculate mean, median, and mode of [1, 2, 2, 3, 4, 4, 4, 5]. Print each on a new line.",
        expected_contains=["3", "4"],  # median=3.5 rounds, mode=4
        difficulty="medium",
        category="math",
    ),
    BenchmarkProblem(
        id="matrix-001",
        name="Matrix Addition",
        task="Add two 2x2 matrices: [[1,2],[3,4]] + [[5,6],[7,8]]. Print the result matrix.",
        expected_contains=["6", "8", "10", "12"],
        difficulty="medium",
        category="math",
    ),
    BenchmarkProblem(
        id="quadratic-001",
        name="Quadratic Formula",
        task="Solve x^2 - 5x + 6 = 0 using the quadratic formula. Print both roots.",
        expected_contains=["2", "3"],
        difficulty="medium",
        category="math",
    ),
    BenchmarkProblem(
        id="power-001",
        name="Power Without Operator",
        task="Write a function to calculate power without using ** or pow(). Calculate 2^10 and print.",
        expected_contains=["1024"],
        difficulty="medium",
        category="math",
    ),
    BenchmarkProblem(
        id="pi-001",
        name="Approximate Pi",
        task="Use the Leibniz formula to approximate pi with 10000 iterations. Print pi rounded to 4 decimal places.",
        expected_contains=["3.14"],
        difficulty="hard",
        category="math",
    ),
]

# =============================================================================
# STRING PROBLEMS
# =============================================================================

STRING_PROBLEMS = [
    BenchmarkProblem(
        id="freq-001",
        name="Character Frequency",
        task="Count the frequency of each character in 'mississippi'. Print as 'char: count' format.",
        expected_contains=["i: 4", "s: 4", "p: 2", "m: 1"],
        difficulty="easy",
        category="strings",
    ),
    BenchmarkProblem(
        id="words-001",
        name="Word Count",
        task="Count words in 'The quick brown fox jumps over the lazy dog'. Print the count.",
        expected_contains=["9"],
        difficulty="easy",
        category="strings",
    ),
    BenchmarkProblem(
        id="longest-001",
        name="Longest Word",
        task="Find the longest word in 'The quick brown fox jumps over the lazy dog'. Print it.",
        expected_contains=["jumps", "quick", "brown"],  # All 5 letters
        difficulty="easy",
        category="strings",
    ),
    BenchmarkProblem(
        id="compress-001",
        name="String Compression",
        task="Compress 'aabcccccaaa' to 'a2b1c5a3'. Print the compressed string.",
        expected_contains=["a2b1c5a3"],
        difficulty="medium",
        category="strings",
    ),
    BenchmarkProblem(
        id="vowels-001",
        name="Vowel Counter",
        task="Count vowels in 'Hello World'. Print the count.",
        expected_contains=["3"],
        difficulty="easy",
        category="strings",
    ),
]

# =============================================================================
# HARD PROBLEMS
# =============================================================================

HARD_PROBLEMS = [
    BenchmarkProblem(
        id="dp-001",
        name="Longest Common Subsequence",
        task="Find the longest common subsequence of 'ABCDGH' and 'AEDFHR'. Print its length.",
        expected_contains=["3"],  # ADH
        difficulty="hard",
        category="dynamic_programming",
    ),
    BenchmarkProblem(
        id="tree-001",
        name="Binary Tree Traversal",
        task="Create a binary tree with root=1, left child=2, right child=3. Left of 2 is 4, right of 2 is 5. Print inorder traversal.",
        expected_contains=["4", "2", "5", "1", "3"],
        difficulty="hard",
        category="data_structures",
    ),
    BenchmarkProblem(
        id="knapsack-001",
        name="0/1 Knapsack",
        task="Solve 0/1 knapsack: weights=[1,2,3], values=[6,10,12], capacity=5. Print max value.",
        expected_contains=["22"],
        difficulty="hard",
        category="dynamic_programming",
        timeout_seconds=10.0,
    ),
    BenchmarkProblem(
        id="graph-001",
        name="Graph BFS",
        task="""Create a graph: A->B, A->C, B->D, C->D, D->E.
Do BFS from A and print nodes in visit order.""",
        expected_contains=["A", "B", "C", "D", "E"],
        difficulty="hard",
        category="data_structures",
    ),
    BenchmarkProblem(
        id="regex-001",
        name="Email Validation",
        task="Write a regex to validate emails. Test 'user@example.com' (valid) and 'invalid@' (invalid). Print True/False.",
        expected_contains=["True", "False"],
        difficulty="medium",
        category="strings",
    ),
]

# =============================================================================
# ALL PROBLEMS
# =============================================================================

BENCHMARK_PROBLEMS: list[BenchmarkProblem] = (
    BASIC_ALGORITHMS
    + ERROR_RECOVERY
    + DATA_MANIPULATION
    + MATH_PROBLEMS
    + STRING_PROBLEMS
    + HARD_PROBLEMS
)

# Problem suites
PROBLEM_SUITES = {
    "quick": BASIC_ALGORITHMS[:5],  # Fast smoke test
    "algorithms": BASIC_ALGORITHMS,
    "error_recovery": ERROR_RECOVERY,
    "data": DATA_MANIPULATION,
    "math": MATH_PROBLEMS,
    "strings": STRING_PROBLEMS,
    "hard": HARD_PROBLEMS,
    "full": BENCHMARK_PROBLEMS,
}


def get_suite(name: str) -> list[BenchmarkProblem]:
    """Get a benchmark suite by name."""
    return PROBLEM_SUITES.get(name, PROBLEM_SUITES["quick"])
