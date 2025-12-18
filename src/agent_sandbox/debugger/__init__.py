"""
EXECUTION TRACE DEBUGGER
========================
Watch the agent think. See every decision.
Step-by-step visualization of the reasoning process.

This is EXPLAINABLE AI - you see the WHY, not just the WHAT.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

log = structlog.get_logger()


class TraceEventType(Enum):
    TASK_START = "task_start"
    THINKING = "thinking"
    CODE_GENERATED = "code_generated"
    EXECUTION_START = "execution_start"
    EXECUTION_SUCCESS = "execution_success"
    EXECUTION_FAILED = "execution_failed"
    CRITIQUE_START = "critique_start"
    CRITIQUE_DONE = "critique_done"
    RETRY = "retry"
    MEMORY_RECALL = "memory_recall"
    SWARM_CONSULT = "swarm_consult"
    TASK_COMPLETE = "task_complete"


@dataclass
class TraceEvent:
    """Single event in execution trace."""

    event_type: TraceEventType
    timestamp: float
    duration_ms: float
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionTrace:
    """Complete trace of an execution."""

    trace_id: str
    task: str
    start_time: float
    events: list[TraceEvent] = field(default_factory=list)
    final_result: dict[str, Any] | None = None

    @property
    def total_duration_ms(self) -> float:
        if not self.events:
            return 0
        return (self.events[-1].timestamp - self.start_time) * 1000

    @property
    def event_count(self) -> int:
        return len(self.events)

    def to_timeline(self) -> list[dict]:
        """Convert to timeline format for visualization."""
        timeline = []
        for e in self.events:
            timeline.append(
                {
                    "time": f"{(e.timestamp - self.start_time) * 1000:.0f}ms",
                    "type": e.event_type.value,
                    "duration": f"{e.duration_ms:.0f}ms",
                    "summary": self._summarize_event(e),
                }
            )
        return timeline

    def _summarize_event(self, e: TraceEvent) -> str:
        data = e.data
        if e.event_type == TraceEventType.CODE_GENERATED:
            return f"Generated {data.get('lines', 0)} lines"
        if e.event_type == TraceEventType.EXECUTION_FAILED:
            return f"Error: {data.get('error', '')[:50]}"
        if e.event_type == TraceEventType.CRITIQUE_DONE:
            return f"Found {data.get('issues', 0)} issues"
        return e.event_type.value.replace("_", " ").title()


class TraceDebugger:
    """
    Records and visualizes execution traces.

    Usage:
        debugger = TraceDebugger()
        with debugger.trace("task description") as trace:
            trace.event(TraceEventType.THINKING, {"thought": "..."})
            # ... do work ...

        print(debugger.visualize(trace))
    """

    def __init__(self):
        self.traces: list[ExecutionTrace] = []
        self._current_trace: ExecutionTrace | None = None
        self._event_start: float | None = None

    def start_trace(self, task: str) -> ExecutionTrace:
        """Start a new execution trace."""
        trace = ExecutionTrace(
            trace_id=f"trace_{int(time.time() * 1000)}",
            task=task,
            start_time=time.time(),
        )
        self._current_trace = trace
        self.traces.append(trace)

        self.event(TraceEventType.TASK_START, {"task": task})
        return trace

    def event(self, event_type: TraceEventType, data: dict[str, Any] = None):
        """Record an event."""
        if not self._current_trace:
            return

        now = time.time()
        duration = 0
        if self._event_start:
            duration = (now - self._event_start) * 1000
        self._event_start = now

        self._current_trace.events.append(
            TraceEvent(
                event_type=event_type,
                timestamp=now,
                duration_ms=duration,
                data=data or {},
            )
        )

    def end_trace(self, result: dict[str, Any] = None):
        """End current trace."""
        if self._current_trace:
            self.event(TraceEventType.TASK_COMPLETE, result or {})
            self._current_trace.final_result = result
        self._current_trace = None
        self._event_start = None

    def visualize(self, trace: ExecutionTrace = None) -> str:
        """Generate ASCII visualization of trace."""
        t = trace or (self.traces[-1] if self.traces else None)
        if not t:
            return "No trace available"

        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            f"║  EXECUTION TRACE: {t.trace_id[:30]:<30}       ║",
            f"║  Task: {t.task[:50]:<50}   ║",
            f"║  Duration: {t.total_duration_ms:.0f}ms | Events: {t.event_count:<20}    ║",
            "╠══════════════════════════════════════════════════════════════╣",
        ]

        for event in t.events:
            icon = self._get_icon(event.event_type)
            time_str = f"{(event.timestamp - t.start_time) * 1000:.0f}ms"
            summary = self._get_summary(event)
            lines.append(f"║  {time_str:>6} {icon} {summary:<48} ║")

        lines.append("╚══════════════════════════════════════════════════════════════╝")
        return "\n".join(lines)

    def _get_icon(self, event_type: TraceEventType) -> str:
        icons = {
            TraceEventType.TASK_START: "🚀",
            TraceEventType.THINKING: "🧠",
            TraceEventType.CODE_GENERATED: "📝",
            TraceEventType.EXECUTION_START: "⚡",
            TraceEventType.EXECUTION_SUCCESS: "✅",
            TraceEventType.EXECUTION_FAILED: "❌",
            TraceEventType.CRITIQUE_START: "🔍",
            TraceEventType.CRITIQUE_DONE: "💡",
            TraceEventType.RETRY: "🔄",
            TraceEventType.MEMORY_RECALL: "🧠",
            TraceEventType.SWARM_CONSULT: "🐝",
            TraceEventType.TASK_COMPLETE: "🎉",
        }
        return icons.get(event_type, "•")

    def _get_summary(self, event: TraceEvent) -> str:
        t = event.event_type
        d = event.data

        if t == TraceEventType.TASK_START:
            return "Starting task..."
        if t == TraceEventType.CODE_GENERATED:
            return f"Generated {d.get('lines', '?')} lines of code"
        if t == TraceEventType.EXECUTION_SUCCESS:
            return "Code executed successfully"
        if t == TraceEventType.EXECUTION_FAILED:
            return f"Failed: {d.get('error', '')[:30]}"
        if t == TraceEventType.CRITIQUE_DONE:
            return f"Found {d.get('issues', 0)} issues"
        if t == TraceEventType.RETRY:
            return f"Retry attempt {d.get('attempt', '?')}"
        if t == TraceEventType.TASK_COMPLETE:
            return f"Complete! Success: {d.get('success', '?')}"

        return t.value.replace("_", " ").title()

    def to_html(self, trace: ExecutionTrace = None) -> str:
        """Generate interactive HTML visualization."""
        t = trace or (self.traces[-1] if self.traces else None)
        if not t:
            return "<p>No trace</p>"

        events_html = []
        for e in t.events:
            icon = self._get_icon(e.event_type)
            time_ms = (e.timestamp - t.start_time) * 1000
            events_html.append(f"""
            <div class="event {e.event_type.value}">
                <span class="icon">{icon}</span>
                <span class="time">{time_ms:.0f}ms</span>
                <span class="label">{self._get_summary(e)}</span>
            </div>""")

        return f"""
        <div class="trace">
            <h3>🔍 Execution Trace</h3>
            <p>Task: {t.task}</p>
            <p>Duration: {t.total_duration_ms:.0f}ms</p>
            <div class="events">{"".join(events_html)}</div>
        </div>"""
