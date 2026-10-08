"""Policy Retrieval Agent: picks the wording version in force on the incident date, then retrieves clauses."""
from __future__ import annotations

import time

from ..models import PolicyVersion
from ..rag import service as rag
from .base import AgentError, ClaimContext, ToolLog


def run(ctx: ClaimContext, log: ToolLog) -> str:
    t = time.perf_counter()
    incident = ctx.facts["incident_date_parsed"]
    versions = ctx.db.query(PolicyVersion).filter_by(policy_id=ctx.insured.policy_id).all()
    match = next((v for v in versions if v.effective_from <= incident <= v.effective_to), None)
    log.record("match_policy_version", {"product": ctx.insured.policy.product_code, "incident_date": incident.isoformat()},
               match.version if match else "no version in force", t)
    if match is None:
        raise AgentError(f"No {ctx.insured.policy.product_code} wording version is in force on {incident}.")
    ctx.version = match
    query = " ".join(str(ctx.facts.get(k, "")) for k in ("diagnosis", "procedure", "narrative", "police_findings"))
    t = time.perf_counter()
    ctx.retrieved = rag.retrieve(ctx.db, query, {match.id}, k=5)
    log.record("hybrid_rag_retrieve", {"query": query[:160], "version_id": match.id},
               ", ".join(f"§{h['clause_ref']}({h['score']})" for h in ctx.retrieved), t)
    return (f"Matched {match.policy.product_code} wording v{match.version} "
            f"({match.effective_from} to {match.effective_to}); retrieved {len(ctx.retrieved)} clauses.")
