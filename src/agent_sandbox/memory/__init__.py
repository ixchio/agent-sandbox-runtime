"""
SELF-EVOLVING MEMORY SYSTEM
===========================
The agent learns from every execution.
Successful solutions are remembered. Failures teach lessons.
Over time, the agent gets smarter.

This is META-LEARNING - the agent improves itself.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()


@dataclass
class MemoryEntry:
    """Single memory of a code execution."""

    task_hash: str
    task: str
    code: str
    success: bool
    attempts: int
    error: str | None
    learned_lesson: str | None
    timestamp: str
    tags: list[str]


@dataclass
class PatternInsight:
    """Learned pattern from multiple executions."""

    pattern: str
    success_rate: float
    occurrences: int
    last_seen: str
    recommended_approach: str


class EvolvingMemory:
    """
    Self-improving memory that learns from execution history.

    Features:
    - Semantic similarity search for past solutions
    - Pattern recognition across failures
    - Auto-generated "lessons learned"
    - Prompt enhancement from history

    The more you use it, the smarter it gets.
    """

    def __init__(self, memory_dir: str = ".agent_memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.memories_file = self.memory_dir / "memories.json"
        self.patterns_file = self.memory_dir / "patterns.json"
        self.memories: list[MemoryEntry] = []
        self.patterns: list[PatternInsight] = []
        self._load()

    def _load(self):
        """Load memories from disk."""
        if self.memories_file.exists():
            data = json.loads(self.memories_file.read_text())
            self.memories = [MemoryEntry(**m) for m in data]
        if self.patterns_file.exists():
            data = json.loads(self.patterns_file.read_text())
            self.patterns = [PatternInsight(**p) for p in data]
        log.info("Memory loaded", memories=len(self.memories), patterns=len(self.patterns))

    def _save(self):
        """Persist memories to disk."""
        self.memories_file.write_text(json.dumps([asdict(m) for m in self.memories], indent=2))
        self.patterns_file.write_text(json.dumps([asdict(p) for p in self.patterns], indent=2))

    def _hash_task(self, task: str) -> str:
        """Create semantic hash of task."""
        normalized = " ".join(task.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:12]

    def remember(
        self,
        task: str,
        code: str,
        success: bool,
        attempts: int = 1,
        error: str | None = None,
    ):
        """Store execution result in memory."""
        # Extract learned lesson
        lesson = None
        if not success and error:
            lesson = self._extract_lesson(task, code, error)

        # Extract tags
        tags = self._extract_tags(task, code)

        entry = MemoryEntry(
            task_hash=self._hash_task(task),
            task=task,
            code=code,
            success=success,
            attempts=attempts,
            error=error,
            learned_lesson=lesson,
            timestamp=datetime.now().isoformat(),
            tags=tags,
        )

        self.memories.append(entry)
        self._update_patterns(entry)
        self._save()

        log.info("Memory stored", success=success, tags=tags)

    def recall(self, task: str, limit: int = 3) -> list[MemoryEntry]:
        """Find similar past tasks."""
        task_words = set(task.lower().split())

        scored = []
        for mem in self.memories:
            mem_words = set(mem.task.lower().split())
            overlap = len(task_words & mem_words)
            if overlap > 0:
                scored.append((overlap, mem))

        scored.sort(key=lambda x: (-x[0], -x[1].success))
        return [m for _, m in scored[:limit]]

    def get_lessons_for_task(self, task: str) -> list[str]:
        """Get relevant lessons from past failures."""
        similar = self.recall(task, limit=5)
        lessons = []
        for mem in similar:
            if not mem.success and mem.learned_lesson:
                lessons.append(mem.learned_lesson)
        return lessons[:3]

    def enhance_prompt(self, task: str, base_prompt: str) -> str:
        """Inject learned knowledge into prompt."""
        similar = self.recall(task, limit=2)
        lessons = self.get_lessons_for_task(task)

        enhancements = []

        # Add successful examples
        successes = [m for m in similar if m.success]
        if successes:
            enhancements.append("SIMILAR SUCCESSFUL SOLUTION:")
            enhancements.append(f"```python\n{successes[0].code[:500]}\n```")

        # Add lessons
        if lessons:
            enhancements.append("\nLEARNED LESSONS (avoid these mistakes):")
            for i, lesson in enumerate(lessons, 1):
                enhancements.append(f"{i}. {lesson}")

        if enhancements:
            return base_prompt + "\n\n--- AGENT MEMORY ---\n" + "\n".join(enhancements)
        return base_prompt

    def _extract_lesson(self, _task: str, _code: str, error: str) -> str:
        """Extract a lesson from failure."""
        error_lower = error.lower()

        if "import" in error_lower or "module" in error_lower:
            return "Import error: Check module names and availability"
        if "syntax" in error_lower:
            return "Syntax error: Validate code structure before execution"
        if "type" in error_lower:
            return "Type error: Ensure correct data types"
        if "index" in error_lower or "key" in error_lower:
            return "Index/Key error: Check bounds and key existence"
        if "timeout" in error_lower:
            return "Timeout: Optimize algorithm or add early termination"

        return f"Failed with: {error[:100]}"

    def _extract_tags(self, task: str, _code: str) -> list[str]:
        """Extract semantic tags from task and code."""
        tags = []

        keywords = {
            "sort": ["sort", "order", "arrange"],
            "search": ["search", "find", "lookup"],
            "math": ["calculate", "sum", "average", "fibonacci", "prime"],
            "string": ["string", "text", "parse", "split"],
            "file": ["file", "read", "write", "csv"],
            "api": ["api", "request", "http", "fetch"],
            "data": ["list", "dict", "array", "json"],
        }

        task_lower = task.lower()
        for tag, words in keywords.items():
            if any(w in task_lower for w in words):
                tags.append(tag)

        return tags[:5]

    def _update_patterns(self, entry: MemoryEntry):
        """Update pattern recognition from new entry."""
        for tag in entry.tags:
            existing = next((p for p in self.patterns if p.pattern == tag), None)
            if existing:
                total = existing.occurrences
                existing.success_rate = (existing.success_rate * total + int(entry.success)) / (
                    total + 1
                )
                existing.occurrences += 1
                existing.last_seen = entry.timestamp
            else:
                self.patterns.append(
                    PatternInsight(
                        pattern=tag,
                        success_rate=1.0 if entry.success else 0.0,
                        occurrences=1,
                        last_seen=entry.timestamp,
                        recommended_approach="",
                    )
                )

    def get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        if not self.memories:
            return {"total": 0}

        successes = sum(1 for m in self.memories if m.success)
        return {
            "total_memories": len(self.memories),
            "success_rate": successes / len(self.memories),
            "patterns_learned": len(self.patterns),
            "top_patterns": sorted(self.patterns, key=lambda p: -p.occurrences)[:5],
        }
