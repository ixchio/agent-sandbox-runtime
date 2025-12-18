"""
FastAPI Application Entry Point
===============================

Main application setup with CORS, routes, and lifecycle management.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_sandbox.api.routes import router as api_router
from agent_sandbox.api.websocket import router as ws_router
from agent_sandbox.config import get_settings
from agent_sandbox.sandbox.manager import SandboxManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
        if get_settings().log_format == "json"
        else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management."""
    settings = get_settings()
    logger.info(
        "Starting Agent Sandbox Runtime",
        version="0.1.0",
        provider=settings.llm_provider,
        model=settings.llm_model,
    )

    # Initialize sandbox manager
    sandbox_manager = SandboxManager(settings)
    await sandbox_manager.initialize()
    app.state.sandbox_manager = sandbox_manager

    logger.info("Sandbox pool initialized", pool_size=settings.sandbox_pool_size)

    yield

    # Cleanup
    logger.info("Shutting down Agent Sandbox Runtime")
    await sandbox_manager.cleanup()


# Create FastAPI application
app = FastAPI(
    title="Agent Sandbox Runtime",
    description="""
    🚀 **Production-grade self-correcting AI agent platform**

    Features:
    - 🔒 Docker-isolated code execution
    - 🔄 Self-healing reflexion loops
    - 📋 Structured output enforcement
    - 📊 Comprehensive benchmarks

    Built with FastAPI, LangGraph, and Docker.
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws")


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "agent-sandbox-runtime",
    }


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "Agent Sandbox Runtime",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
