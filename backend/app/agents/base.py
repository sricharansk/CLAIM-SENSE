"""Shared agent context. Each agent is a bounded function: explicit inputs, explicit tools, logged tool calls."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from ..models import Claim, InsuredPolicy, PolicyVersion


class AgentError(Exception):
    """Raised when an agent cannot proceed safely (missing evidence, invalid input)."""


@dataclass
class ClaimContext:
    db: Session
    claim: Claim
    correlation_id: str
    facts: dict[str, Any] = field(default_factory=dict)
    fact_sources: dict[str, dict] = field(default_factory=dict)
    line_items: list[dict] = field(default_factory=list)
    doc_types: list[str] = field(default_factory=list)
    insured: InsuredPolicy | None = None
    version: PolicyVersion | None = None
    retrieved: list[dict] = field(default_factory=list)
    coverage: dict = field(default_factory=dict)
    adjudication: dict = field(default_factory=dict)
    risk: dict = field(default_factory=dict)
    evidence: list[dict] = field(default_factory=list)
    recommendation: dict = field(default_factory=dict)


class ToolLog:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def record(self, tool: str, args: dict, result_summary: str, started: float) -> None:
        self.calls.append({"tool": tool, "args": args, "result": result_summary,
                           "ms": int((time.perf_counter() - started) * 1000)})
