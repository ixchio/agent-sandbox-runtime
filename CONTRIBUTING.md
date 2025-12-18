# Contributing to Agent Sandbox Runtime

Thank you for your interest in contributing! 🎉 This project is open source under the MIT License, and we welcome contributions from everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Coding Standards](#coding-standards)
- [Documentation](#documentation)

---

## Code of Conduct

Be kind, be respectful, and have fun building! We're here to learn and create together.

- **Be inclusive**: Welcome newcomers and help them get started
- **Be constructive**: Provide helpful feedback, not criticism
- **Be patient**: Not everyone has the same experience level
- **Be collaborative**: We're all working toward the same goal

---

## Getting Started

### Prerequisites

- **Python 3.11+** - [Download](https://python.org/downloads)
- **Docker** - [Install](https://docs.docker.com/get-docker/) (required for sandbox execution)
- **Git** - [Install](https://git-scm.com/)
- **An LLM API key** - We recommend [Groq](https://console.groq.com) (free)

### Quick Setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/agent-sandbox-runtime.git
cd agent-sandbox-runtime

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install with dev dependencies
pip install -e ".[dev]"

# 4. Set up pre-commit hooks
pre-commit install

# 5. Configure environment
cp .env.example .env
# Add your GROQ_API_KEY to .env

# 6. Verify setup
pytest tests/unit/ -v --tb=short
```

---

## Development Setup

### Environment Variables

Create a `.env` file with these minimum settings:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
```

### Docker Setup (for sandbox testing)

```bash
# Build the sandbox image
docker build -t agent-sandbox-python:latest -f docker/Dockerfile.sandbox .

# Verify Docker is working
docker run --rm agent-sandbox-python:latest python -c "print('Hello from sandbox')"
```

### IDE Setup

We recommend VS Code with these extensions:
- Python (Microsoft)
- Ruff (charliermarsh)
- Docker (Microsoft)

Settings (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff"
    }
}
```

---

## Project Architecture

```
src/agent_sandbox/
├── api/              # FastAPI endpoints
├── cli.py            # Command-line interface (Typer)
├── config.py         # Settings & environment (Pydantic)
├── orchestrator/     # LangGraph workflow
│   ├── graph.py      # Main state machine
│   └── nodes/        # Generate, Execute, Critique, Retry
├── providers/        # LLM adapters (6 providers)
├── sandbox/          # Docker execution engine
│   ├── manager.py    # Container lifecycle
│   └── executor.py   # Code execution
├── swarm/            # Multi-agent intelligence
└── runtime.py        # Main entry point
```

### Key Concepts

| Concept | Location | Description |
|---------|----------|-------------|
| **Reflexion Loop** | `orchestrator/graph.py` | Generate → Execute → Critique → Retry cycle |
| **Sandbox Manager** | `sandbox/manager.py` | Docker container pool & execution |
| **LLM Provider** | `providers/*.py` | Unified interface for 6 LLM backends |
| **Swarm Intelligence** | `swarm/__init__.py` | Multi-agent collaboration |

For detailed architecture, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Making Changes

### Branch Naming

```
feature/add-new-provider    # New feature
fix/docker-timeout-bug      # Bug fix
docs/update-readme          # Documentation
refactor/simplify-sandbox   # Code refactor
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Azure OpenAI provider
fix: handle Docker timeout gracefully
docs: add API reference documentation
refactor: simplify sandbox manager
test: add integration tests for providers
chore: update dependencies
```

### Development Workflow

```bash
# 1. Create a branch
git checkout -b feature/your-feature

# 2. Make changes

# 3. Run linting & formatting
ruff check src/ --fix
ruff format src/

# 4. Run tests
pytest tests/unit/ -v

# 5. Commit
git commit -m "feat: your feature description"

# 6. Push
git push origin feature/your-feature

# 7. Open Pull Request on GitHub
```

---

## Testing

### Test Structure

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Tests with Docker (slower)
└── e2e/            # End-to-end tests (requires API key)
```

### Running Tests

```bash
# Unit tests (fast, no external deps)
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=src/agent_sandbox --cov-report=html

# Integration tests (requires Docker)
pytest tests/integration/ -v --slow

# Specific test file
pytest tests/unit/test_providers.py -v

# Specific test
pytest tests/unit/test_sandbox.py::test_execute_simple -v
```

### Writing Tests

```python
# tests/unit/test_example.py
import pytest
from agent_sandbox.config import Settings

def test_settings_defaults():
    """Test that default settings are applied correctly."""
    settings = Settings()
    assert settings.llm_provider == "groq"
    assert settings.max_reflexion_attempts == 3

@pytest.mark.asyncio
async def test_async_operation():
    """Test async functionality."""
    result = await some_async_function()
    assert result is not None

@pytest.mark.slow
def test_docker_execution():
    """Integration test requiring Docker."""
    # This test is skipped unless --slow flag is used
    pass
```

---

## Pull Request Process

### Before Submitting

- [ ] Run `ruff check src/ --fix` (linting)
- [ ] Run `ruff format src/` (formatting)
- [ ] Run `pytest tests/unit/ -v` (tests pass)
- [ ] Update documentation if needed
- [ ] Add tests for new functionality

### PR Template

When you open a PR, include:

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactor

## Testing
How did you test these changes?

## Related Issues
Fixes #123
```

### Review Process

1. **Automated checks**: CI runs linting, formatting, and tests
2. **Maintainer review**: Usually within a few days
3. **Feedback**: Address any requested changes
4. **Merge**: Once approved, we'll merge!

---

## Issue Guidelines

### Bug Reports

Use this template:

```markdown
## Bug Description
Clear description of the bug.

## Steps to Reproduce
1. Run `agent-sandbox run "..."`
2. See error

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Environment
- OS: Ubuntu 22.04
- Python: 3.11.0
- Docker: 24.0.0
- Provider: groq
```

### Feature Requests

```markdown
## Feature Description
What feature would you like?

## Use Case
Why is this useful?

## Proposed Solution
How do you think it should work?

## Alternatives Considered
Any other approaches you've thought of?
```

---

## Coding Standards

### Style Guide

We use **Ruff** for linting and formatting:

```bash
# Check for issues
ruff check src/

# Auto-fix issues
ruff check src/ --fix

# Format code
ruff format src/
```

### Key Rules

1. **Type hints**: All functions should have type annotations
   ```python
   def execute(self, code: str, timeout: float = 5.0) -> ExecutionResult:
   ```

2. **Docstrings**: All public functions need docstrings
   ```python
   def execute(self, code: str) -> ExecutionResult:
       """Execute code in the Docker sandbox.
       
       Args:
           code: Python code to execute
           
       Returns:
           Execution result with stdout, stderr, and exit code
       """
   ```

3. **Error handling**: Use specific exceptions
   ```python
   try:
       result = await self.sandbox.execute(code)
   except docker.errors.ContainerError as e:
       logger.error("Container failed", error=str(e))
       raise SandboxExecutionError(str(e)) from e
   ```

4. **Async conventions**: Use `async`/`await` for I/O operations
   ```python
   async def generate(self, prompt: str) -> str:
       response = await self.client.generate(prompt)
       return response.content
   ```

---

## Documentation

### Updating Docs

When you make changes:

1. **New feature**: Add to relevant doc in `docs/`
2. **API change**: Update `docs/API.md`
3. **Architecture change**: Update `docs/ARCHITECTURE.md`

### Doc Structure

| File | Purpose |
|------|---------|
| `README.md` | Project overview & quick start |
| `docs/ARCHITECTURE.md` | System design |
| `docs/HOW_IT_WORKS.md` | Deep dive into mechanics |
| `docs/CAPABILITIES.md` | What it can/can't do |
| `docs/index.html` | Web documentation page |

### Writing Style

- Use **clear, simple language**
- Include **code examples**
- Add **diagrams** for complex concepts
- Keep sections **short and scannable**

---

## Need Help?

- 💬 **Discussions**: [GitHub Discussions](https://github.com/ixchio/agent-sandbox-runtime/discussions)
- 🐛 **Issues**: [GitHub Issues](https://github.com/ixchio/agent-sandbox-runtime/issues)
- 📧 **Email**: amankumarpandeyin@gmail.com

---

## Recognition

Contributors are recognized in:
- The [README.md](README.md) contributors section
- GitHub's contributor graph
- Release notes for significant contributions

Thank you for making Agent Sandbox Runtime better! 🚀
