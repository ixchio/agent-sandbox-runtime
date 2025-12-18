import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog

from agent_sandbox.config import Settings, get_settings
from agent_sandbox.providers import LLMProvider, create_provider
from agent_sandbox.sandbox.manager import ExecutionRequest, SandboxManager

log = structlog.get_logger()


class CognitiveBias(Enum):
    PRECISE = "precise"
    SPEED = "speed"
    CREATIVE = "creative"
    ROBUST = "robust"
    MINIMAL = "minimal"


@dataclass
class Universe:
    id: str
    bias: CognitiveBias
    code: str = ""
    result: Any = None
    survival_score: float = 0.0
    status: str = "superposition"


@dataclass
class QuantumState:
    task: str
    universes: list[Universe]
    super_solution: str | None = None
    entropy: float = 1.0


BIAS_PROMPTS = {
    CognitiveBias.PRECISE: """
    MODE: PRECISE
    Prioritize absolute correctness, type safety, and formal logic.
    Use type hints, assertions, and strict validation.
    Better safe than fast.
    """,
    CognitiveBias.SPEED: """
    MODE: SPEED
    Prioritize raw performance and O(n) complexity.
    Use algorithmic tricks, caching, and fast built-ins.
    Ignore safety if it slows things down. Speed is god.
    """,
    CognitiveBias.CREATIVE: """
    MODE: CREATIVE
    Think outside the box. Use unexpected libraries or mathematical properties.
    Find a clever shortcut that no one else sees.
    """,
    CognitiveBias.ROBUST: """
    MODE: ROBUST
    Assume everything will fail. Handle all exceptions.
    Data validation is key. Never crash.
    """,
    CognitiveBias.MINIMAL: """
    MODE: MINIMAL
    Write the smallest, most elegant code possible.
    Memory efficiency is paramount. No bloat.
    """,
}


class QuantumFluxEngine:
    """
    Manages the lifecycle of parallel thought universes.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._provider: LLMProvider | None = None
        self.sandbox = SandboxManager(self.settings)

    @property
    def provider(self) -> LLMProvider:
        if not self._provider:
            self._provider = create_provider(
                self.settings.llm_provider,
                self.settings.get_provider_api_key(),
                self.settings.get_provider_model(),
            )
        return self._provider

    async def initialize(self):
        """Initialize resources."""
        await self.sandbox.initialize()

    async def cleanup(self):
        """Cleanup resources."""
        await self.sandbox.cleanup()

    async def collapse_wavefunction(self, task: str) -> dict[str, Any]:
        """
        Run the Quantum Cognitive Loop.
        1. Spawn Universes
        2. Parallel Execution
        3. Collapsing Score
        4. Entanglement
        """
        # Ensure sandbox is initialized
        if not self.sandbox._initialized:
            await self.initialize()

        log.info("🌊 QUANTUM FLUX INITIATED", task=task[:50])

        # 1. Spawn Universes (Superposition)
        universes = [
            Universe(id="U_PRECISE", bias=CognitiveBias.PRECISE),
            Universe(id="U_SPEED", bias=CognitiveBias.SPEED),
            Universe(id="U_ROBUST", bias=CognitiveBias.ROBUST),
        ]

        # 2. Parallel Generation (Multiverse Expansion)
        await self._expand_multiverse(task, universes)

        # 3. Parallel Execution (Reality Testing)
        await self._test_realities(universes)

        # 4. Score & Filter (Wavefunction Collapse)
        survivors = self._calculate_survival(universes)
        log.info("🌌 Wavefunction Collapsed", survivors=len(survivors))

        if not survivors:
            return {"error": "All universes imploded due to high entropy (bugs)."}

        # 5. Entanglement (Merge best traits)
        super_solution = await self._entangle_logic(task, survivors)

        return {
            "super_solution": super_solution,
            "multiverse_stats": {
                u.id: {
                    "score": u.survival_score,
                    "result": u.result.status.value if u.result else "void",
                }
                for u in universes
            },
            "winning_reality": survivors[0].id if survivors else "entropy",
        }

    async def _expand_multiverse(self, task: str, universes: list[Universe]):
        """Generate code for each universe in parallel."""

        async def generate_reality(u: Universe):
            system = f"""You are a Python expert in {u.bias.name} mode.

            {BIAS_PROMPTS[u.bias]}

            Task: {task}

            Output strictly strictly strict JSON: {{ "code": "..." }}
            """
            try:
                resp = await self.provider.generate_json(system, f"Task: {task}")
                data = json.loads(resp.content)
                u.code = data.get("code", "")
                log.info(f"✨ Universe {u.id} Born", len=len(u.code))
            except Exception as e:
                log.error(f"Universe {u.id} Failed Big Bang", error=str(e))

        await asyncio.gather(*[generate_reality(u) for u in universes])

    async def _test_realities(self, universes: list[Universe]):
        """Run code in parallel sandboxes."""

        async def run_simulation(u: Universe):
            if not u.code:
                return
            try:
                # We assume the code is self-contained or we wrap it
                # For this MVP, we assume the code prints something or defines functions
                # To test it, we might need test cases.
                # For now, we check if it RUNS without syntax error.
                result = await self.sandbox.execute(ExecutionRequest(code=u.code))
                u.result = result
                log.info(f"⚡ Universe {u.id} Simulated", exit_code=result.exit_code)
            except Exception as e:
                log.error(f"Universe {u.id} Simulation Error", error=str(e))

        await asyncio.gather(*[run_simulation(u) for u in universes])

    def _calculate_survival(self, universes: list[Universe]) -> list[Universe]:
        """Score universes based on their bias and execution result."""
        for u in universes:
            if not u.result or u.result.exit_code != 0:
                u.survival_score = 0.0
                continue

            score = 0.5  # Base score for running

            # Simple heuristic scoring based on bias
            if u.bias == CognitiveBias.SPEED:
                score += 0.3  # Assume we validated speed elsewhere, potential for improvement
            elif u.bias == CognitiveBias.PRECISE:
                if "typing" in u.code or "def" in u.code:
                    score += 0.2
            elif u.bias == CognitiveBias.ROBUST and "try" in u.code and "except" in u.code:
                score += 0.3

            u.survival_score = score

        # Sort by score
        survivors = [u for u in universes if u.survival_score > 0]
        survivors.sort(key=lambda x: -x.survival_score)
        return survivors

    async def _entangle_logic(self, task: str, survivors: list[Universe]) -> str:
        """Merge the logic of survivors into a super-solution."""
        if len(survivors) == 1:
            return survivors[0].code

        log.info("🔗 Entangling Realities...", count=len(survivors))

        # We ask the LLM to act as the "Entangler"
        best_codes = "\n\n".join([f"--- REALITY {u.id} ---\n{u.code}" for u in survivors])

        system = """You are the QUANTUM ENTANGLER.
        You see parallel timeline solutions to a problem.
        Your job is to MERGE them into a perfect SUPER-SOLUTION.

        Take the:
        - TYPE SAFETY of Precise Reality
        - SPEED of Speed Reality
        - SAFETY of Robust Reality

        Synthesize the perfect code.
        """

        prompt = f"Task: {task}\n\nParallel Solutions:\n{best_codes}\n\nCreate the Super-Solution."

        resp = await self.provider.generate_json(system, prompt)
        data = json.loads(resp.content)
        return data.get("code", "")
