"""
LangGraph Agent Workflow
========================

The core state machine that orchestrates the reflexion loop.

This is the "FLOW ENGINEERING" that makes this project stand out.
The workflow implements:

1. GENERATE → Code generation with Groq LLM
2. EXECUTE  → Sandboxed Docker execution
3. CRITIQUE → Error analysis and feedback (if failed)
4. RETRY    → Loop back with improvements (up to N times)

Visual Representation:

    ┌─────────────┐
    │   START     │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │  GENERATE   │◄────────────┐
    └──────┬──────┘             │
           │                    │
           ▼                    │
    ┌─────────────┐             │
    │   EXECUTE   │             │
    └──────┬──────┘             │
           │                    │
     ┌─────┴─────┐              │
     │ success?  │              │
     └─────┬─────┘              │
           │                    │
    ┌──────┴───────┐            │
    │              │            │
    ▼              ▼            │
┌───────┐    ┌─────────┐        │
│SUCCESS│    │ CRITIQUE│────────┤
└───────┘    └─────────┘        │
                                │
                   ┌────────────┘
                   │ (retry if possible)
                   ▼
              ┌─────────┐
              │  RETRY  │
              └─────────┘
"""

from typing import Any

import structlog
from langgraph.graph import END, StateGraph

from agent_sandbox.config import Settings, get_settings
from agent_sandbox.orchestrator.nodes.critic import CriticNode
from agent_sandbox.orchestrator.nodes.executor import ExecutorNode
from agent_sandbox.orchestrator.nodes.generator import GeneratorNode
from agent_sandbox.orchestrator.nodes.retry import RetryManagerNode
from agent_sandbox.sandbox.manager import SandboxManager

logger = structlog.get_logger()


# Type for the state dict used in the graph
GraphState = dict[str, Any]


def create_agent_graph(
    sandbox_manager: SandboxManager,
    settings: Settings | None = None,
) -> StateGraph:
    """
    Create the LangGraph workflow for the agent.

    Args:
        sandbox_manager: Initialized sandbox manager for code execution
        settings: Optional settings override

    Returns:
        Compiled StateGraph ready for execution
    """
    settings = settings or get_settings()

    # Initialize nodes
    generator = GeneratorNode(settings)
    executor = ExecutorNode(settings=settings)
    executor.set_sandbox_manager(sandbox_manager)
    critic = CriticNode(settings)
    retry_manager = RetryManagerNode(max_attempts=settings.max_reflexion_attempts)

    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("generate", generator.generate)
    workflow.add_node("execute", executor.execute)
    workflow.add_node("critique", critic.critique)
    workflow.add_node("retry", retry_manager.process)
    workflow.add_node("finalize", finalize_result)

    # Set entry point
    workflow.set_entry_point("generate")

    # Add edges
    workflow.add_edge("generate", "execute")

    # Conditional edge from execute
    workflow.add_conditional_edges(
        "execute",
        executor.should_continue,
        {
            "success": "finalize",
            "critique": "critique",
            "end": "finalize",
        },
    )

    workflow.add_edge("critique", "retry")

    # Conditional edge from retry
    workflow.add_conditional_edges(
        "retry",
        retry_manager.should_continue,
        {
            "generate": "generate",
            "end": "finalize",
        },
    )

    workflow.add_edge("finalize", END)

    logger.info("Agent graph created")

    return workflow.compile()


async def finalize_result(state: GraphState) -> GraphState:
    """
    Finalize the workflow result.

    Prepares the final output to return to the user.
    """
    execution_result = state.get("execution_result", {})
    exit_code = execution_result.get("exit_code", 1)
    stdout = execution_result.get("stdout", "")
    stderr = execution_result.get("stderr", "")

    success = exit_code == 0 and not execution_result.get("timed_out", False)

    if success:
        final_output = stdout
    else:
        final_output = (
            f"Execution failed after {state.get('attempt', 1)} attempts.\n\nLast error:\n{stderr}"
        )

    logger.info(
        "Workflow finalized",
        success=success,
        attempts=state.get("attempt", 1),
    )

    return {
        "completed": True,
        "success": success,
        "final_output": final_output,
    }


class AgentGraph:
    """
    High-level wrapper for the agent workflow.

    Provides a simple interface for running the reflexion loop.
    """

    def __init__(
        self,
        sandbox_manager: SandboxManager,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.sandbox_manager = sandbox_manager
        self.graph = create_agent_graph(sandbox_manager, settings)

    async def run(
        self,
        task: str,
        max_attempts: int | None = None,
    ) -> dict[str, Any]:
        """
        Run the agent on a task.

        Args:
            task: The task description
            max_attempts: Optional override for max retry attempts

        Returns:
            Final state with results
        """
        initial_state: GraphState = {
            "task": task,
            "code": "",
            "dependencies": [],
            "reasoning": "",
            "confidence": 0.0,
            "execution_result": None,
            "critique": None,
            "should_retry": False,
            "attempt": 0,
            "max_attempts": max_attempts or self.settings.max_reflexion_attempts,
            "history": [],
            "completed": False,
            "success": False,
            "final_output": None,
        }

        logger.info("Starting agent workflow", task=task[:100])

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        logger.info(
            "Agent workflow completed",
            success=final_state.get("success"),
            attempts=final_state.get("attempt"),
        )

        return final_state

    async def run_streaming(
        self,
        task: str,
        max_attempts: int | None = None,
    ):
        """
        Run the agent with streaming updates.

        Yields state updates as the workflow progresses.
        """
        initial_state: GraphState = {
            "task": task,
            "code": "",
            "dependencies": [],
            "reasoning": "",
            "confidence": 0.0,
            "execution_result": None,
            "critique": None,
            "should_retry": False,
            "attempt": 0,
            "max_attempts": max_attempts or self.settings.max_reflexion_attempts,
            "history": [],
            "completed": False,
            "success": False,
            "final_output": None,
        }

        logger.info("Starting streaming agent workflow", task=task[:100])

        # Stream updates
        async for event in self.graph.astream(initial_state):
            yield event
