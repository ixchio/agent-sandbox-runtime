# How It Works

A deep dive into the runtime mechanics of Agent Sandbox Runtime.

## The Complete Request Lifecycle

When you run `agent-sandbox run "Calculate fibonacci(10)"`, here's exactly what happens:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REQUEST LIFECYCLE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CLI PARSING                                                             │
│     └── Typer parses command → creates task string                          │
│                                                                             │
│  2. RUNTIME INITIALIZATION                                                  │
│     └── Load .env → Create Settings → Initialize SandboxManager             │
│     └── Warm Docker container pool (pre-create containers)                  │
│                                                                             │
│  3. LANGGRAPH WORKFLOW                                                      │
│     └── Create state machine → Set initial state → Start execution          │
│                                                                             │
│  4. [GENERATE NODE]                                                         │
│     └── Build prompt with task + examples                                   │
│     └── Call LLM (e.g., Groq llama-3.3-70b)                                 │
│     └── Parse response → Extract code + dependencies + reasoning            │
│                                                                             │
│  5. [EXECUTE NODE]                                                          │
│     └── Get container from pool (or create new)                             │
│     └── Inject code into container /tmp/code.py                             │
│     └── Run with timeout: python /tmp/code.py                               │
│     └── Capture stdout, stderr, exit_code                                   │
│     └── Return container to pool                                            │
│                                                                             │
│  6. [DECISION]                                                              │
│     ├── exit_code == 0? → SUCCESS → Go to step 9                            │
│     └── exit_code != 0? → FAILURE → Continue to step 7                      │
│                                                                             │
│  7. [CRITIQUE NODE] (only if failed)                                        │
│     └── Build critique prompt with code + error                             │
│     └── Call LLM to analyze why it failed                                   │
│     └── Extract specific issues and suggested fixes                         │
│                                                                             │
│  8. [RETRY NODE]                                                            │
│     ├── attempt < max_attempts? → Loop back to step 4 with feedback         │
│     └── attempt >= max_attempts? → Give up → Go to step 9                   │
│                                                                             │
│  9. [FINALIZE]                                                              │
│     └── Package results → Return to user                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## The Reflexion Loop in Detail

### What is Reflexion?

Reflexion is a self-improvement technique where an AI agent:
1. Attempts a task
2. Gets feedback (success/failure + error messages)
3. Reflects on what went wrong
4. Tries again with learned knowledge

This mimics how humans learn from mistakes.

### How We Implement It

```python
# Simplified from orchestrator/graph.py

class ReflexionLoop:
    def run(self, task: str) -> Result:
        state = {"task": task, "attempt": 0, "history": []}
        
        while state["attempt"] < MAX_ATTEMPTS:
            # GENERATE: Create code from task description
            code = self.generator.generate(
                task=state["task"],
                previous_failures=state["history"]  # Learning from mistakes
            )
            
            # EXECUTE: Run in Docker sandbox
            result = self.sandbox.execute(code)
            
            if result.success:
                return result  # Done!
            
            # CRITIQUE: Analyze what went wrong
            critique = self.critic.analyze(
                code=code,
                error=result.stderr,
                output=result.stdout
            )
            
            # Learn from this attempt
            state["history"].append({
                "code": code,
                "error": result.stderr,
                "critique": critique
            })
            
            state["attempt"] += 1
        
        return Result(success=False, message="Max retries exceeded")
```

### Real Example: Self-Correction in Action

**Task**: "Calculate the 10th Fibonacci number"

**Attempt 1** (LLM generates):
```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
```

**Execution**: ✅ Success (output: `55`)

---

**Task**: "Read data from users.json and print usernames"

**Attempt 1** (LLM generates):
```python
import json
with open('users.json') as f:
    data = json.load(f)
for user in data:
    print(user['username'])
```

**Execution**: ❌ Failed
```
FileNotFoundError: [Errno 2] No such file or directory: 'users.json'
```

**Critique** (LLM analyzes):
```
The code assumes 'users.json' exists. In a sandbox environment, no files 
exist by default. The code should either:
1. Create sample data inline
2. Handle the FileNotFoundError gracefully
```

**Attempt 2** (LLM self-corrects):
```python
import json

# Create sample data since file doesn't exist in sandbox
sample_data = [
    {"username": "alice", "id": 1},
    {"username": "bob", "id": 2},
    {"username": "charlie", "id": 3}
]

for user in sample_data:
    print(user['username'])
```

**Execution**: ✅ Success

## Docker Sandbox Deep Dive

### Why Docker?

| Approach | Security | Speed | Isolation |
|----------|----------|-------|-----------|
| `eval()` | ❌ Dangerous | ⚡ Fast | ❌ None |
| `subprocess` | ⚠️ Limited | ⚡ Fast | ⚠️ Process-level |
| **Docker** | ✅ Strong | ✓ Good | ✅ Full OS-level |

### Container Configuration

```python
# From sandbox/manager.py

container = docker.containers.run(
    image="agent-sandbox-python:latest",
    command=["python", "/tmp/code.py"],
    
    # RESOURCE LIMITS
    mem_limit="256m",         # 256MB max memory
    memswap_limit="256m",     # No swap
    cpu_period=100000,
    cpu_quota=50000,          # 0.5 CPU cores
    
    # SECURITY
    network_disabled=True,    # No internet access
    read_only=True,           # Read-only filesystem
    security_opt=["no-new-privileges"],
    cap_drop=["ALL"],         # Drop all capabilities
    
    # ISOLATION
    tmpfs={"/tmp": "size=64m"},  # RAM-backed /tmp
    volumes={code_path: {"bind": "/tmp/code.py", "mode": "ro"}},
    
    # EXECUTION
    detach=True,
    remove=True,
)
```

### Container Pool (Performance Optimization)

Creating Docker containers takes ~500ms. To achieve sub-second responses, we pre-warm a pool:

```
┌────────────────────────────────────────────────────┐
│                  CONTAINER POOL                    │
│                                                    │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│   │Container│ │Container│ │Container│ │Container│ │
│   │  #1     │ │  #2     │ │  #3     │ │  #4     │ │
│   │ (ready) │ │ (ready) │ │ (in-use)│ │ (ready) │ │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
│       ▲                        │                   │
│       │                        │                   │
│   Return after              Executing             │
│   execution                 user code              │
│                                                    │
└────────────────────────────────────────────────────┘
```

## LLM Provider Abstraction

### The Interface

All 6 providers implement the same interface:

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> GenerateResponse:
        """Generate text completion."""
        pass
    
    @abstractmethod
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict | None = None,
    ) -> GenerateResponse:
        """Generate JSON-structured completion."""
        pass
```

### Provider Selection at Runtime

```python
# From providers/__init__.py

def create_provider(provider_name: str, api_key: str, model: str) -> LLMProvider:
    providers = {
        "groq": GroqProvider,
        "openrouter": OpenRouterProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
    }
    
    provider_class = providers[provider_name]
    return provider_class(api_key=api_key, model=model)
```

## Structured Output Parsing

### The Problem

LLMs return text. We need structured data.

### Our Solution

1. **System prompt** instructs LLM to output JSON
2. **Pydantic models** validate the response
3. **Retry** if parsing fails

```python
# From orchestrator/nodes/generator.py

class GeneratedCode(BaseModel):
    code: str
    dependencies: list[str]
    reasoning: str
    confidence: float

async def generate(self, state: GraphState) -> GraphState:
    response = await self.provider.generate_json(
        system_prompt=GENERATOR_PROMPT,
        user_prompt=state["task"],
    )
    
    # Parse and validate
    generated = GeneratedCode.model_validate_json(response.content)
    
    return {
        "code": generated.code,
        "dependencies": generated.dependencies,
        "reasoning": generated.reasoning,
        "confidence": generated.confidence,
    }
```

## Error Handling Philosophy

### Graceful Degradation

```python
# Every external call is wrapped in try/except

async def execute(self, code: str) -> ExecutionResult:
    try:
        container = await self._get_container()
        result = await self._run_code(container, code)
        return ExecutionResult(success=True, output=result.stdout)
    
    except docker.errors.ContainerError as e:
        # Container crashed - return error for critique
        return ExecutionResult(success=False, error=str(e))
    
    except asyncio.TimeoutError:
        # Timeout - kill container, return timeout error
        return ExecutionResult(success=False, error="Execution timed out")
    
    except Exception as e:
        # Unexpected - log and return generic error
        logger.exception("Unexpected error in sandbox")
        return ExecutionResult(success=False, error="Internal error")
```

### Retry at Every Level

1. **LLM calls**: Retry with exponential backoff on rate limits
2. **Docker operations**: Retry container creation on Docker failures
3. **Reflexion loop**: Retry entire generation on code failures

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Container pool warm-up | ~2s (one-time) | Creates 5 pre-warmed containers |
| LLM generation (Groq) | ~500-1000ms | Depends on prompt length |
| Container execution | ~100-200ms | Using pre-warmed container |
| Error critique | ~300-500ms | Smaller prompt |
| **Total (success)** | **~700-1200ms** | Single attempt |
| **Total (with retry)** | **~1500-3000ms** | 2 attempts |

## Observability

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

# Every significant operation is logged
logger.info(
    "Code generated",
    task=task[:100],
    code_lines=code.count('\n'),
    confidence=generated.confidence,
    provider=self.settings.llm_provider,
)
```

### Log Output Example

```
2024-12-19 12:00:01 [info] Agent workflow started task="Calculate fibonacci(10)"
2024-12-19 12:00:01 [info] Code generated code_lines=8 confidence=0.95
2024-12-19 12:00:02 [info] Sandbox execution started container_id="abc123"
2024-12-19 12:00:02 [info] Execution complete exit_code=0 duration_ms=134
2024-12-19 12:00:02 [info] Agent workflow completed success=true attempts=1
```
