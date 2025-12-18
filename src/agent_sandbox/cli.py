"""
CLI Interface
=============

Command-line interface for the agent sandbox runtime.
"""

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

app = typer.Typer(
    name="agent-sandbox",
    help="🚀 Self-correcting AI agent with sandboxed execution",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    task: str = typer.Argument(..., help="Task for the agent to solve"),
    max_attempts: int = typer.Option(3, "--attempts", "-a", help="Max retry attempts"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Run the agent on a task.

    Example:
        agent-sandbox run "Write a fibonacci function"
    """
    asyncio.run(_run_task(task, max_attempts, verbose))


async def _run_task(task: str, max_attempts: int, verbose: bool):
    """Run task asynchronously."""
    from agent_sandbox.runtime import AgentRuntime

    console.print(
        Panel.fit(
            f"[bold blue]Task:[/bold blue] {task}",
            title="🚀 Agent Sandbox Runtime",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task("Initializing...", total=None)

        try:
            async with AgentRuntime() as runtime:
                progress.update(task_id, description="Running agent...")

                result = await runtime.run(task, max_attempts)

        except Exception as e:
            progress.stop()
            console.print(f"\n[red]Error:[/red] {str(e)}")
            raise typer.Exit(1)

    # Display results
    if result["success"]:
        console.print("\n[green]✓ Success![/green]")
    else:
        console.print("\n[red]✗ Failed[/red]")

    console.print(f"\n[dim]Attempts:[/dim] {result['attempts']}")

    if result["code"]:
        console.print("\n[bold]Generated Code:[/bold]")
        syntax = Syntax(result["code"], "python", theme="monokai", line_numbers=True)
        console.print(syntax)

    if result["output"]:
        console.print("\n[bold]Output:[/bold]")
        console.print(Panel(result["output"], border_style="green" if result["success"] else "red"))

    if verbose and result["reasoning"]:
        console.print("\n[bold]Reasoning:[/bold]")
        console.print(result["reasoning"])


@app.command()
def benchmark(
    suite: str = typer.Option("quick", "--suite", "-s", help="Benchmark suite"),
    limit: int | None = typer.Option(None, "--limit", "-l", help="Limit problems"),
):
    """
    Run benchmark suite.

    Example:
        agent-sandbox benchmark --suite full
    """
    asyncio.run(_run_benchmark(suite, limit))


async def _run_benchmark(suite: str, limit: int | None):
    """Run benchmark asynchronously."""
    from agent_sandbox.runtime import AgentRuntime

    console.print(
        Panel.fit(
            f"[bold blue]Suite:[/bold blue] {suite}",
            title="📊 Benchmark Runner",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Running benchmarks...", total=None)

        async with AgentRuntime() as runtime:
            results = await runtime.run_benchmark(suite, limit)

    # Display results
    table = Table(title="Benchmark Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Tests", str(results.total_tests))
    table.add_row("Passed", str(results.passed))
    table.add_row("Failed", str(results.failed))
    table.add_row("Success Rate", f"{results.success_rate:.1%}")
    table.add_row("Avg Attempts", f"{results.average_attempts:.2f}")
    table.add_row("Avg Time", f"{results.average_execution_time_ms:.0f}ms")
    table.add_row("vs Baseline", f"{results.improvement_over_baseline:+.1f}%")

    console.print(table)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
):
    """
    Start the API server.

    Example:
        agent-sandbox serve --port 8000
    """
    import uvicorn

    console.print(
        Panel.fit(
            f"[bold blue]Starting server at http://{host}:{port}[/bold blue]",
            title="🌐 Agent Sandbox API",
        )
    )

    uvicorn.run(
        "agent_sandbox.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def demo():
    """
    Run an interactive demo.
    """
    asyncio.run(_run_demo())


async def _run_demo():
    """Run demo asynchronously."""
    from agent_sandbox.runtime import AgentRuntime

    console.print(
        Panel.fit(
            "[bold green]Welcome to Agent Sandbox Runtime Demo![/bold green]\n\n"
            "Watch the agent write code, execute it in a sandbox,\n"
            "and self-correct any errors.",
            title="🎬 Demo",
        )
    )

    # Demo task that will likely need correction
    demo_task = """
    Write a Python function that:
    1. Downloads the content from https://httpbin.org/json (use requests library)
    2. Parses the JSON response
    3. Prints the "slideshow" title from the response

    Note: Make sure to handle any potential errors.
    """

    console.print(f"\n[bold]Task:[/bold]\n{demo_task}")

    console.print("\n[yellow]Press Enter to start...[/yellow]")
    input()

    async with AgentRuntime() as runtime:
        attempt = 0
        async for event in runtime.run_streaming(demo_task):
            for node_name, data in event.items():
                attempt = data.get("attempt", attempt)

                if node_name == "generate":
                    console.print(f"\n[blue]📝 Attempt {attempt}: Generating code...[/blue]")
                    if data.get("code"):
                        syntax = Syntax(data["code"], "python", theme="monokai")
                        console.print(syntax)

                elif node_name == "execute":
                    result = data.get("execution_result", {})
                    if result.get("exit_code") == 0:
                        console.print("[green]✓ Execution successful![/green]")
                        if result.get("stdout"):
                            console.print(Panel(result["stdout"], border_style="green"))
                    else:
                        console.print("[red]✗ Execution failed[/red]")
                        if result.get("stderr"):
                            console.print(Panel(result["stderr"][:500], border_style="red"))

                elif node_name == "critique":
                    console.print("\n[yellow]🔍 Analyzing error...[/yellow]")
                    if data.get("critique"):
                        console.print(data["critique"][:300])

                elif node_name == "finalize":
                    if data.get("success"):
                        console.print("\n[bold green]🎉 Task completed successfully![/bold green]")
                    else:
                        console.print("\n[bold red]Task failed after all attempts[/bold red]")

    console.print("\n[dim]Demo complete. Run 'agent-sandbox --help' for more options.[/dim]")


if __name__ == "__main__":
    app()
