"""
Agent Sandbox Runtime
======================

Production-grade self-correcting AI agent platform with sandboxed execution.

Features:
- 🔒 Docker-isolated code execution
- 🔄 Self-healing reflexion loops (LangGraph)
- 📋 Pydantic-enforced structured outputs
- 📊 Comprehensive evaluation pipeline
- ⚡ Async-first architecture (FastAPI)

Example:
    >>> from agent_sandbox import AgentRuntime
    >>> runtime = AgentRuntime()
    >>> result = await runtime.execute("Write a function to calculate fibonacci")
    >>> print(result.code)
"""

__version__ = "0.1.0"
__author__ = "ixchio and contributors"

from agent_sandbox.config import Settings
from agent_sandbox.runtime import AgentRuntime

__all__ = [
    "Settings",
    "AgentRuntime",
    "__version__",
]
