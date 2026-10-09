"""Relational source of truth (blueprint PART 11). Money is stored as Numeric(14, 2)."""
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

Money = Numeric(14, 2)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(60), unique=True)
    display_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20))  # ADJUSTER | SUPERVISOR | AUDITOR
    approval_limit: Mapped[Decimal | None] = mapped_column(Money, nullable=True)  # None = unlimited
    password_hash: Mapped[str] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(default=True)


class Policy(Base):
    """An insurance product (e.g. a health plan) with dated wording versions."""

    __tablename__ = "policies"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    line_of_business: Mapped[str] = mapped_column(String(20))
    insurer: Mapped[str] = mapped_column(String(200))
    synthetic: Mapped[bool] = mapped_column(default=True)
    versions: Mapped[list["PolicyVersion"]] = relationship(back_populates="policy", order_by="PolicyVersion.effective_from")


class PolicyVersion(Base):
    __tablename__ = "policy_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"))
    version: Mapped[str] = mapped_column(String(20))
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date] = mapped_column(Date)
    source_file: Mapped[str] = mapped_column(String(300))
    terms: Mapped[dict] = mapped_column(JSON)
    policy: Mapped[Policy] = relationship(back_populates="versions")
    clauses: Mapped[list["PolicyClause"]] = relationship(back_populates="version", order_by="PolicyClause.id")


class PolicyIngestion(Base):
    """One attempt to ingest a policy wording, with its processing states (UPLOADED → … → READY or FAILED)."""
    __tablename__ = "policy_ingestions"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(300))
    file_type: Mapped[str] = mapped_column(String(10), default="")
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="UPLOADED")
    stages: Mapped[list] = mapped_column(JSON, default=list)
    product_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    policy_version_id: Mapped[int | None] = mapped_column(ForeignKey("policy_versions.id"), nullable=True)
    pages: Mapped[int] = mapped_column(Integer, default=0)
    clauses: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String(60), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PolicyClause(Base):
    __tablename__ = "policy_clauses"
    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("policy_versions.id"))
    clause_ref: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    section: Mapped[str] = mapped_column(String(200))
    page: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    version: Mapped[PolicyVersion] = relationship(back_populates="clauses")


class InsuredPolicy(Base):
    """A customer's policy contract (policy number) issued on a product."""

    __tablename__ = "insured_policies"
    id: Mapped[int] = mapped_column(primary_key=True)
    policy_number: Mapped[str] = mapped_column(String(40), unique=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"))
    holder_name: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    sum_insured: Mapped[Decimal] = mapped_column(Money)
    policy: Mapped[Policy] = relationship()


class Claim(Base):
    __tablename__ = "claims"
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_number: Mapped[str] = mapped_column(String(40), unique=True)
    policy_number: Mapped[str] = mapped_column(String(40))
    claim_type: Mapped[str] = mapped_column(String(20))
    claimant_name: Mapped[str] = mapped_column(String(200))
    incident_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    claimed_amount: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    documents: Mapped[list["ClaimDocument"]] = relationship(back_populates="claim", order_by="ClaimDocument.id")
    facts: Mapped[list["ClaimFact"]] = relationship(back_populates="claim", order_by="ClaimFact.id")


class ClaimDocument(Base):
    __tablename__ = "claim_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"))
    filename: Mapped[str] = mapped_column(String(300))
    doc_type: Mapped[str] = mapped_column(String(40), default="unknown")
    storage_path: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text, default="")
    pages: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="UPLOADED")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    claim: Mapped[Claim] = relationship(back_populates="documents")


class ClaimFact(Base):
    __tablename__ = "claim_facts"
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"))
    document_id: Mapped[int | None] = mapped_column(ForeignKey("claim_documents.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(60))
    value: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(default=1.0)
    source_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_text: Mapped[str] = mapped_column(Text, default="")
    claim: Mapped[Claim] = relationship(back_populates="facts")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"))
    correlation_id: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="RUNNING")
    policy_version_id: Mapped[int | None] = mapped_column(ForeignKey("policy_versions.id"), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules_version: Mapped[str] = mapped_column(String(40))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="analysis_run", order_by="AgentRun.id")


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(ForeignKey("analysis_runs.id"))
    agent: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20))
    summary: Mapped[str] = mapped_column(Text, default="")
    tool_calls: Mapped[list] = mapped_column(JSON, default=list)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="agent_runs")


class ClaimDecision(Base):
    """Either the AI recommendation (source=AI) or a human reviewer decision (source=HUMAN)."""

    __tablename__ = "claim_decisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"))
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(10))
    decision: Mapped[str] = mapped_column(String(30))
    payable_amount: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    actor: Mapped[str] = mapped_column(String(100))
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"))
    queue: Mapped[str] = mapped_column(String(30))
    priority: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    assignee: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int | None] = mapped_column(ForeignKey("claims.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40))
    actor: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    correlation_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DatasetSource(Base):
    __tablename__ = "dataset_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    publisher: Mapped[str] = mapped_column(String(200))
    year: Mapped[str] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(String(400))
    purpose: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(60))
