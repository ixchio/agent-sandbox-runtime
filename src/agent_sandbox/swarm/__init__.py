"""
SWARM INTELLIGENCE ENGINE
=========================
Multi-agent collaboration with specialist roles.
Each agent has expertise - they debate and synthesize solutions.

This is BEYOND simple LLM calls. This is emergent intelligence.
"""

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog

from agent_sandbox.config import Settings, get_settings
from agent_sandbox.providers import LLMProvider, create_provider

log = structlog.get_logger()


class AgentRole(Enum):
    ARCHITECT = "architect"  # Designs solution structure
    CODER = "coder"  # Writes implementation
    CRITIC = "critic"  # Finds bugs and edge cases
    OPTIMIZER = "optimizer"  # Improves performance
    SECURITY = "security"  # Checks for vulnerabilities


@dataclass
class AgentVote:
    role: AgentRole
    decision: str
    confidence: float
    reasoning: str


ROLE_PROMPTS = {
    AgentRole.ARCHITECT: """You are the ARCHITECT agent.
Your job: Design the high-level structure before coding.
Think about: modules, functions, data flow, edge cases.
Be concise. Output JSON: {"design": "...", "confidence": 0.9}""",
    AgentRole.CODER: """You are the CODER agent.
Your job: Write clean, working Python code.
Follow the architect's design. Handle edge cases.
Output JSON: {"code": "...", "reasoning": "...", "confidence": 0.9}""",
    AgentRole.CRITIC: """You are the CRITIC agent.
Your job: Find bugs, edge cases, potential failures.
Be harsh but constructive. Find what others missed.
Output JSON: {"issues": [...], "severity": "high/medium/low", "confidence": 0.9}""",
    AgentRole.OPTIMIZER: """You are the OPTIMIZER agent.
Your job: Make code faster, cleaner, more Pythonic.
Suggest specific improvements with reasoning.
Output JSON: {"improvements": [...], "optimized_code": "...", "confidence": 0.9}""",
    AgentRole.SECURITY: """You are the SECURITY agent.
Your job: Find security vulnerabilities.
Check: injection, unsafe operations, data leaks.
Output JSON: {"vulnerabilities": [...], "safe": true/false, "confidence": 0.9}""",
}


class SwarmIntelligence:
    """
    Multi-agent swarm that collaborates on complex tasks.

    Flow:
    1. Architect designs solution
    2. Coder implements
    3. Critic reviews
    4. Optimizer improves
    5. Security validates
    6. Synthesize final result

    Agents vote and debate until consensus.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._provider: LLMProvider | None = None
        self.debate_rounds = 2
        self.consensus_threshold = 0.7

    @property
    def provider(self) -> LLMProvider:
        if not self._provider:
            self._provider = create_provider(
                self.settings.llm_provider,
                self.settings.get_provider_api_key(),
                self.settings.get_provider_model(),
            )
        return self._provider

    async def solve(self, task: str) -> dict[str, Any]:
        """Run the full swarm intelligence pipeline."""
        log.info("Swarm activated", task=task[:50])

        # Phase 1: Architecture
        design = await self._consult_agent(AgentRole.ARCHITECT, task)
        log.info("Architect done", confidence=design.get("confidence"))

        # Phase 2: Implementation
        code_prompt = f"Task: {task}\n\nArchitect's Design:\n{design.get('design', '')}"
        implementation = await self._consult_agent(AgentRole.CODER, code_prompt)
        code = implementation.get("code", "")
        log.info("Coder done", lines=code.count("\n"))

        # Phase 3: Parallel Review (Critic + Security)
        review_prompt = f"Task: {task}\n\nCode:\n```python\n{code}\n```"
        critic_task = self._consult_agent(AgentRole.CRITIC, review_prompt)
        security_task = self._consult_agent(AgentRole.SECURITY, review_prompt)

        critic_result, security_result = await asyncio.gather(critic_task, security_task)

        issues = critic_result.get("issues", [])
        vulnerabilities = security_result.get("vulnerabilities", [])

        log.info("Review done", issues=len(issues), vulns=len(vulnerabilities))

        # Phase 4: Optimization (if code is safe)
        if security_result.get("safe", True) and len(issues) < 3:
            opt_prompt = f"Task: {task}\n\nCode:\n```python\n{code}\n```\n\nIssues found: {issues}"
            optimized = await self._consult_agent(AgentRole.OPTIMIZER, opt_prompt)
            final_code = optimized.get("optimized_code", code)
        else:
            final_code = code

        # Calculate swarm confidence
        confidences = [
            design.get("confidence", 0.5),
            implementation.get("confidence", 0.5),
            critic_result.get("confidence", 0.5),
            security_result.get("confidence", 0.5),
        ]
        swarm_confidence = sum(confidences) / len(confidences)

        return {
            "code": final_code,
            "design": design.get("design", ""),
            "issues": issues,
            "vulnerabilities": vulnerabilities,
            "swarm_confidence": swarm_confidence,
            "agents_consulted": 5,
            "consensus": swarm_confidence >= self.consensus_threshold,
        }

    async def _consult_agent(self, role: AgentRole, context: str) -> dict:
        """Get response from a specialist agent."""
        system = ROLE_PROMPTS[role]

        try:
            resp = await self.provider.generate_json(
                system_prompt=system,
                user_prompt=context,
                temperature=0.3,
                max_tokens=2048,
            )
            return json.loads(resp.content)
        except Exception as e:
            log.warning("Agent failed", role=role.value, error=str(e))
            return {"error": str(e), "confidence": 0.0}

    async def debate(self, task: str, proposal: str) -> dict[str, Any]:
        """
        Agents debate a proposal until consensus.
        Each agent votes, then they see each other's votes and revote.
        """
        votes: list[AgentVote] = []

        for round_num in range(self.debate_rounds):
            round_votes = await self._voting_round(task, proposal, votes)
            votes = round_votes

            # Check consensus
            avg_conf = sum(v.confidence for v in votes) / len(votes)
            if avg_conf >= self.consensus_threshold:
                log.info("Consensus reached", round=round_num + 1, confidence=avg_conf)
                break

        return {
            "consensus": avg_conf >= self.consensus_threshold,
            "final_confidence": avg_conf,
            "votes": [
                {"role": v.role.value, "decision": v.decision, "confidence": v.confidence}
                for v in votes
            ],
        }

    async def _voting_round(
        self, task: str, proposal: str, prev_votes: list[AgentVote]
    ) -> list[AgentVote]:
        """Single round of voting."""
        context = f"Task: {task}\n\nProposal:\n{proposal}"
        if prev_votes:
            context += "\n\nPrevious votes:\n" + "\n".join(
                f"- {v.role.value}: {v.decision} (conf: {v.confidence})" for v in prev_votes
            )

        async def get_vote(role: AgentRole) -> AgentVote:
            resp = await self._consult_agent(
                role, context + "\n\nYour vote (approve/reject with reasoning):"
            )
            return AgentVote(
                role=role,
                decision=resp.get("decision", "abstain"),
                confidence=resp.get("confidence", 0.5),
                reasoning=resp.get("reasoning", ""),
            )

        tasks = [
            get_vote(role) for role in [AgentRole.ARCHITECT, AgentRole.CRITIC, AgentRole.SECURITY]
        ]
        return await asyncio.gather(*tasks)
