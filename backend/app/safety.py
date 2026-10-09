"""Detects text in uploaded documents that is addressed to an AI system rather than to a claims handler.

Uploaded documents are untrusted data. Nothing in them is ever executed or followed: amounts come from the rules
engine and decisions from humans. This scan only makes manipulation attempts visible to the reviewer.
"""
from __future__ import annotations

import re

PATTERNS = [
    re.compile(r"\b(ignore|disregard|forget|override)\b[^.\n]{0,40}\b(previous|prior|above|earlier|all|any|your)\b[^.\n]{0,20}"
               r"\b(instructions?|rules|prompts?|guidelines)\b", re.I),
    re.compile(r"\b(system|developer) prompt\b", re.I),
    re.compile(r"\b(you are|act as|pretend to be)\s+(an?\s+)?(ai|assistant|language model|llm|chatbot|claims? bot)\b", re.I),
    re.compile(r"\b(note|message|instructions?)\s+(to|for)\s+(the\s+)?(ai|assistant|model|llm|bot|automated (system|reviewer))\b", re.I),
    re.compile(r"\b(approve|pay|settle)\b[^.\n]{0,30}\bclaim\b[^.\n]{0,30}\b(in full|immediately|without (review|checks?|verification))\b", re.I),
]


def embedded_instructions(text: str) -> list[dict]:
    """Return one finding per line that looks like an instruction to an AI system."""
    found = []
    for n, line in enumerate(text.splitlines(), start=1):
        if any(p.search(line) for p in PATTERNS):
            found.append({"line": n, "text": line.strip()[:200]})
    return found
