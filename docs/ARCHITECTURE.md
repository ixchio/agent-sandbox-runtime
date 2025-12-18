# System Architecture

## Overview

Agent Sandbox Runtime is a modular, production-grade AI agent platform built with clear separation of concerns. Each component has a single responsibility and communicates through well-defined interfaces.

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           AGENT SANDBOX RUNTIME                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐ │
│  │     CLI      │    │   REST API   │    │         WebSocket            │ │
│  │  (typer)     │    │  (FastAPI)   │    │        (streaming)           │ │
│  └──────┬───────┘    └──────┬───────┘    └─────────────┬────────────────┘ │
│         │                   │                          │                   │
│         └───────────────────┼──────────────────────────┘                   │
│                             │                                              │
│                             ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                          RUNTIME LAYER                               │ │
│  │              (agent_sandbox/runtime.py - Entry Point)                │ │
│  └───────────────────────────────┬──────────────────────────────────────┘ │
│                                  │                                         │
│         ┌────────────────────────┼────────────────────────┐               │
│         │                        │                        │               │
│         ▼                        ▼                        ▼               │
│  ┌─────────────┐    ┌────────────────────┐    ┌─────────────────────────┐│
│  │   CONFIG    │    │    ORCHESTRATOR    │    │     SWARM INTEL         ││
│  │ (Settings)  │    │    (LangGraph)     │    │  (Multi-Agent)          ││
│  └─────────────┘    └─────────┬──────────┘    └───────────────┬─────────┘│
│                               │                               │          │
│                    ┌──────────┴──────────┐                    │          │
│                    │                     │                    │          │
│                    ▼                     ▼                    ▼          │
│  ┌─────────────────────────┐  ┌──────────────────┐   ┌────────────────┐ │
│  │      LLM PROVIDERS      │  │     SANDBOX      │   │    MEMORY      │ │
│  │  (Groq, OpenRouter,     │  │    (Docker)      │   │   (Qdrant)     │ │
│  │   Anthropic, etc.)      │  │                  │   │                │ │
│  └─────────────────────────┘  └──────────────────┘   └────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Entry Points

#### CLI (`agent_sandbox/cli.py`)
Command-line interface built with Typer. Provides commands:
- `agent-sandbox run "task"` - Execute a single task
- `agent-sandbox serve` - Start the API server
- `agent-sandbox benchmark` - Run benchmark suite

#### API (`agent_sandbox/api/`)
FastAPI-based REST and WebSocket server:
- `POST /execute` - Submit a task for execution
- `WS /stream` - Real-time streaming of execution progress
- `GET /health` - Health check endpoint

### 2. Runtime (`agent_sandbox/runtime.py`)

The main entry point that initializes all components and provides a unified interface:

```python
from agent_sandbox import AgentRuntime

runtime = AgentRuntime()
result = await runtime.execute("Write a function to sort a list")
```

### 3. Orchestrator (`agent_sandbox/orchestrator/`)

The heart of the system - a LangGraph state machine that implements the reflexion loop.

#### State Machine Nodes

| Node | File | Responsibility |
|------|------|----------------|
| **Generator** | `nodes/generator.py` | Calls LLM to generate Python code |
| **Executor** | `nodes/executor.py` | Runs code in Docker sandbox |
| **Critic** | `nodes/critic.py` | Analyzes failures, suggests fixes |
| **Retry** | `nodes/retry.py` | Manages retry logic and limits |

#### State Flow

```python
# Simplified state transitions (graph.py)
workflow.set_entry_point("generate")
workflow.add_edge("generate", "execute")
workflow.add_conditional_edges("execute", {
    "success": "finalize",
    "critique": "critique"
})
workflow.add_edge("critique", "retry")
workflow.add_conditional_edges("retry", {
    "generate": "generate",  # Loop back
    "end": "finalize"
})
```

### 4. Sandbox (`agent_sandbox/sandbox/`)

Docker-based isolated execution environment.

#### Components

| Component | File | Purpose |
|-----------|------|---------|
| **Manager** | `manager.py` | Container lifecycle, pool warming |
| **Executor** | `executor.py` | Code injection and execution |
| **Models** | `models.py` | Request/Response types |

#### Security Model

```
┌───────────────────────────────────────────────────────────┐
│                    HOST SYSTEM                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              DOCKER CONTAINER                       │ │
│  │  ┌───────────────────────────────────────────────┐ │ │
│  │  │           SANDBOXED EXECUTION                 │ │ │
│  │  │  • Memory limit: 256MB                        │ │ │
│  │  │  • CPU limit: 0.5 cores                       │ │ │
│  │  │  • Network: disabled                          │ │ │
│  │  │  • Timeout: 5 seconds                         │ │ │
│  │  │  • Read-only filesystem (except /tmp)         │ │ │
│  │  │  • No privileged operations                   │ │ │
│  │  └───────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

### 5. Providers (`agent_sandbox/providers/`)

Unified interface for multiple LLM backends:

| Provider | File | Models |
|----------|------|--------|
| Groq | `groq_provider.py` | Llama 3.3, Mixtral |
| OpenRouter | `openrouter_provider.py` | 100+ models |
| Anthropic | `anthropic_provider.py` | Claude 3.5 |
| Google | `google_provider.py` | Gemini 1.5/2.0 |
| OpenAI | `openai_provider.py` | GPT-4o |
| Ollama | `ollama_provider.py` | Local models |

All providers implement the `LLMProvider` interface:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str: ...
    
    @abstractmethod
    async def generate_json(self, prompt: str) -> dict: ...
```

### 6. Swarm Intelligence (`agent_sandbox/swarm/`)

Multi-agent collaboration system with 5 specialist roles:

```
┌─────────────────────────────────────────────────────────────┐
│                    SWARM PIPELINE                           │
│                                                             │
│  ┌──────────┐   Design    ┌────────┐   Implement  ┌──────┐ │
│  │ARCHITECT │────────────►│ CODER  │─────────────►│      │ │
│  └──────────┘             └────────┘              │      │ │
│                                                   │      │ │
│  ┌──────────┐                                     │FINAL │ │
│  │  CRITIC  │────────────────────────────────────►│      │ │
│  └──────────┘   Review                            │CODE  │ │
│                                                   │      │ │
│  ┌──────────┐                                     │      │ │
│  │ SECURITY │────────────────────────────────────►│      │ │
│  └──────────┘   Validate                          │      │ │
│                                                   │      │ │
│  ┌──────────┐                                     │      │ │
│  │OPTIMIZER │────────────────────────────────────►│      │ │
│  └──────────┘   Improve                           └──────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Each agent has a specialized prompt and votes on proposals until consensus.

### 7. Configuration (`agent_sandbox/config.py`)

Pydantic-based settings with environment variable loading:

```python
class Settings(BaseSettings):
    llm_provider: str = "groq"
    groq_api_key: str | None = None
    sandbox_timeout_seconds: float = 5.0
    max_reflexion_attempts: int = 3
    # ... etc
    
    model_config = SettingsConfigDict(env_file=".env")
```

## Design Principles

### 1. Dependency Injection
Components receive their dependencies through constructors, enabling testing and flexibility.

### 2. Async-First
All I/O operations are async, enabling concurrent LLM calls and non-blocking execution.

### 3. Structured Outputs
LLM responses are parsed into Pydantic models, ensuring type safety.

### 4. Fail-Safe Defaults
Sandbox defaults to restrictive settings (no network, low memory) for security.

### 5. Observable
Structured logging with `structlog` provides detailed execution traces.

## Extending the System

### Adding a New LLM Provider

1. Create `providers/your_provider.py`
2. Implement the `LLMProvider` interface
3. Register in `providers/__init__.py`
4. Add config options to `config.py`

### Adding a New Swarm Agent

1. Add role to `AgentRole` enum in `swarm/__init__.py`
2. Define role prompt in `ROLE_PROMPTS`
3. Include in the swarm pipeline

### Adding New Orchestrator Nodes

1. Create `orchestrator/nodes/your_node.py`
2. Implement the node function
3. Add to graph in `orchestrator/graph.py`
