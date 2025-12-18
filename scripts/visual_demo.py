#!/usr/bin/env python3
"""
VISUAL DEMO
===========
Demonstrates the TraceDebugger system with a simulated complex task.
Generates an interactive HTML report.
"""

import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_sandbox.debugger import TraceDebugger, TraceEventType

console = Console(record=True)


def simulate_demo():
    debugger = TraceDebugger()

    task_desc = "Implement a Recursive Fractal Tree using Python's Turtle library. Depth: 6."
    console.print(Panel(f"[bold yellow]{task_desc}[/bold yellow]", title="🚀 NEW TASK"))

    # Start Trace
    trace = debugger.start_trace(task_desc)

    # 1. Memory Recall
    console.print("[cyan]🧠 Querying Memory...[/cyan]")
    debugger.event(
        TraceEventType.MEMORY_RECALL,
        {
            "query": "recursive fractal visualization",
            "matches": ["Koch Snowflake (98% match)", "Sierpinski Triangle (85% match)"],
        },
    )
    time.sleep(1)

    # 2. Thinking
    console.print("[magenta]🤔 Planning Solution...[/magenta]")
    thoughts = [
        "Decomposing problem into recursive sub-structures.",
        "Need a function `draw_branch(length, depth)`.",
        "Base case: if depth == 0, stop.",
        "Recursive step: Forward -> Turn Right -> Recurse -> Turn Left -> Recurse -> Restore State.",
    ]
    for thought in thoughts:
        debugger.event(TraceEventType.THINKING, {"thought": thought})
        time.sleep(0.5)

    # 3. Code Generation
    console.print("[green]📝 Generating Code...[/green]")
    code = """import turtle

def draw_branch(t, branch_length, angle, depth):
    if depth == 0:
        return

    # Draw the main branch
    t.forward(branch_length)
    
    # Right sub-tree
    t.right(angle)
    draw_branch(t, branch_length * 0.7, angle, depth - 1)
    
    # Left sub-tree
    t.left(angle * 2)
    draw_branch(t, branch_length * 0.7, angle, depth - 1)
    
    # Restore orientation
    t.right(angle)
    t.backward(branch_length)

def main():
    t = turtle.Turtle()
    t.speed(0)
    t.left(90)
    t.up()
    t.backward(100)
    t.down()
    t.color("green")
    
    draw_branch(t, 100, 20, 6)
    turtle.done()

if __name__ == "__main__":
    main()
"""
    debugger.event(
        TraceEventType.CODE_GENERATED,
        {"language": "python", "lines": len(code.splitlines()), "snippet": code},
    )
    time.sleep(1)

    # 4. Critique
    console.print("[yellow]🔍 Reviewing Code...[/yellow]")
    debugger.event(TraceEventType.CRITIQUE_START)
    time.sleep(0.5)
    debugger.event(
        TraceEventType.CRITIQUE_DONE,
        {"issues": 0, "verdict": "Safe to execute", "complexity": "O(2^n)"},
    )

    # 5. Execution
    console.print("[blue]⚡ Executing...[/blue]")
    debugger.event(TraceEventType.EXECUTION_START, {"environment": "sandbox-docker"})
    time.sleep(1.5)
    debugger.event(
        TraceEventType.EXECUTION_SUCCESS,
        {"output": "GUI Window Opened", "artifacts": ["fractal_tree.png"]},
    )

    # 6. Complete
    console.print("[bold green]✅ Task Complete![/bold green]")
    debugger.end_trace({"success": True, "quality_score": 0.98})

    # Generate Report
    html_content = debugger.to_html()

    # Enhance HTML with some CSS for the demo
    html_content = html_content.replace(
        "<style>",
        "<style>body { font-family: sans-serif; background: #1a1a2e; color: #fff; padding: 20px; } "
        ".event { background: #16213e; margin: 10px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #0f3460; } "
        ".icon { font-size: 1.5em; margin-right: 10px; } "
        ".time { color: #e94560; font-family: monospace; font-weight: bold; margin-right: 15px; } "
        ".label { font-size: 1.1em; } "
        "h3 { color: #4ade80; border-bottom: 2px solid #4ade80; padding-bottom: 10px; }",
    )

    output_path = Path("trace_report.html")
    output_path.write_text(html_content)
    console.print(f"\n[bold]📄 Trace saved to: {output_path.absolute()}[/bold]")

    # Save Terminal Recording
    terminal_html = Path("terminal_demo.html")
    console.save_html(str(terminal_html), theme=None)
    console.print(f"[bold]🎥 Terminal recording saved to: {terminal_html.absolute()}[/bold]")

    return output_path


if __name__ == "__main__":
    simulate_demo()
