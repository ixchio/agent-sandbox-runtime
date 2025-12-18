# Contributing to Agent Sandbox Runtime

Thank you for your interest in contributing! 🎉

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/agent-sandbox-runtime.git
   cd agent-sandbox-runtime
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Copy environment file**
   ```bash
   cp .env.example .env
   # Add your GROQ_API_KEY
   ```

## Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=src/agent_sandbox

# Integration tests (requires Docker)
pytest tests/integration/ -v --slow
```

## Code Style

We use:
- **Ruff** for linting and formatting
- **MyPy** for type checking

```bash
# Lint
ruff check src/

# Format
ruff format src/

# Type check
mypy src/
```

## Pull Request Process

1. Create a feature branch
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make your changes

3. Ensure tests pass
   ```bash
   pytest tests/unit/ -v
   ```

4. Update documentation if needed

5. Submit a pull request

## Code of Conduct

Be kind, be respectful, and have fun building! 🚀
