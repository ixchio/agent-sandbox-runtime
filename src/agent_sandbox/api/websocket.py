"""
WebSocket Streaming
===================

Real-time streaming of agent execution via WebSocket.
"""

import contextlib
from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from agent_sandbox.config import get_settings
from agent_sandbox.orchestrator.graph import AgentGraph

logger = structlog.get_logger()

router = APIRouter(tags=["websocket"])


class StreamMessage(BaseModel):
    """Message sent over WebSocket."""

    type: str  # "status", "code", "execution", "error", "complete"
    data: dict[str, Any]
    timestamp: str = ""

    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**data)


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected", total=len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected", total=len(self.active_connections))

    async def send_message(self, websocket: WebSocket, message: StreamMessage) -> None:
        await websocket.send_json(message.model_dump())

    async def broadcast(self, message: StreamMessage) -> None:
        for connection in self.active_connections:
            await connection.send_json(message.model_dump())


manager = ConnectionManager()


@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming agent execution.

    Protocol:
    1. Client connects
    2. Client sends: {"task": "...", "max_attempts": 3}
    3. Server streams updates as agent executes
    4. Server sends final result and closes

    Message types:
    - "connected" - Connection established
    - "started" - Execution started
    - "generating" - Code generation in progress
    - "code" - Generated code
    - "executing" - Running in sandbox
    - "execution_result" - Sandbox result
    - "critiquing" - Analyzing error
    - "retrying" - Starting retry
    - "complete" - Final result
    - "error" - Error occurred
    """
    await manager.connect(websocket)

    try:
        # Send connected message
        await manager.send_message(
            websocket,
            StreamMessage(type="connected", data={"message": "Connected to agent stream"}),
        )

        # Wait for task
        data = await websocket.receive_json()
        task = data.get("task", "")
        max_attempts = data.get("max_attempts", 3)

        if not task:
            await manager.send_message(
                websocket,
                StreamMessage(type="error", data={"message": "No task provided"}),
            )
            return

        logger.info("Starting streaming execution", task=task[:50])

        # Send started message
        await manager.send_message(
            websocket,
            StreamMessage(type="started", data={"task": task}),
        )

        # Get sandbox manager from app state
        # Note: This requires the WebSocket to have access to app state
        # In production, you'd inject this properly
        settings = get_settings()

        from agent_sandbox.sandbox.manager import SandboxManager

        sandbox_manager = SandboxManager(settings)
        await sandbox_manager.initialize()

        try:
            agent = AgentGraph(sandbox_manager, settings)

            # Stream execution
            async for event in agent.run_streaming(task, max_attempts):
                # Parse event and send appropriate message
                for node_name, node_output in event.items():
                    if node_name == "generate":
                        await manager.send_message(
                            websocket,
                            StreamMessage(
                                type="code",
                                data={
                                    "code": node_output.get("code", ""),
                                    "reasoning": node_output.get("reasoning", ""),
                                    "attempt": node_output.get("attempt", 1),
                                },
                            ),
                        )

                    elif node_name == "execute":
                        result = node_output.get("execution_result", {})
                        await manager.send_message(
                            websocket,
                            StreamMessage(
                                type="execution_result",
                                data={
                                    "exit_code": result.get("exit_code", 1),
                                    "stdout": result.get("stdout", ""),
                                    "stderr": result.get("stderr", ""),
                                    "timed_out": result.get("timed_out", False),
                                },
                            ),
                        )

                    elif node_name == "critique":
                        await manager.send_message(
                            websocket,
                            StreamMessage(
                                type="critique",
                                data={
                                    "critique": node_output.get("critique", ""),
                                    "should_retry": node_output.get("should_retry", False),
                                },
                            ),
                        )

                    elif node_name == "finalize":
                        await manager.send_message(
                            websocket,
                            StreamMessage(
                                type="complete",
                                data={
                                    "success": node_output.get("success", False),
                                    "output": node_output.get("final_output", ""),
                                },
                            ),
                        )

        finally:
            await sandbox_manager.cleanup()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        with contextlib.suppress(Exception):
            await manager.send_message(
                websocket,
                StreamMessage(type="error", data={"message": str(e)}),
            )
    finally:
        manager.disconnect(websocket)
