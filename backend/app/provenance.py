"""Data provenance: the source registry validator (blueprint Data Prompt A) and the RAG ingestion manifest
(Data Prompt G). A source without provenance is rejected; a clause chunk that cannot be traced to a source file,
version, page, section/clause and extraction run is kept out of the retrieval index."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from sqlalchemy.orm import Session

from .config import settings
from .models import PolicyClause, PolicyIngestion, PolicyVersion

REQUIRED = ("id", "name", "publisher", "source_type", "data_type", "url", "publication_date", "license",
            "intended_use", "status")
SOURCE_TYPES = {"synthetic", "regulatory", "statistical", "benchmark"}
STATUSES = {"IN_USE", "REGISTERED"}
USES = {"rag", "adjudication", "demo", "evaluation", "analytics", "calibration", "benchmark"}
DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


class ProvenanceError(ValueError):
    pass


def registry_path() -> Path:
    return settings.data_dir / "source_registry.json"


def _files(root: Path, paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for rel in paths:
        p = root / rel
        out.extend(sorted(f for f in p.rglob("*") if f.is_file()) if p.is_dir() else [p])
    return out


def tree_sha256(root: Path, paths: list[str]) -> str:
    """SHA-256 over (relative path, file SHA-256) pairs, so a source spanning many files has one stable checksum."""
    h = hashlib.sha256()
    for f in _files(root, paths):
        h.update(f"{f.relative_to(root).as_posix()}\0{hashlib.sha256(f.read_bytes()).hexdigest()}\n".encode())
    return h.hexdigest()


def validate_source(s: dict, root: Path) -> list[str]:
    """Problems with one registry entry; an empty list means its provenance is complete."""
    sid = s.get("id") or "(no id)"
    problems = [f"{sid}: missing {k}" for k in REQUIRED if s.get(k) in (None, "", [])]
    if s.get("source_type") and s["source_type"] not in SOURCE_TYPES:
        problems.append(f"{sid}: unknown source_type {s['source_type']}")
    if s.get("status") and s["status"] not in STATUSES:
        problems.append(f"{sid}: unknown status {s['status']}")
    if unknown := sorted(set(s.get("intended_use") or []) - USES):
        problems.append(f"{sid}: unknown intended_use {', '.join(unknown)}")
    for k in ("publication_date", "retrieval_date"):
        if s.get(k) and not DATE_RE.match(str(s[k])):
            problems.append(f"{sid}: {k} must be YYYY, YYYY-MM or YYYY-MM-DD")
    if s.get("status") == "IN_USE":
        if not s.get("retrieval_date"):
            problems.append(f"{sid}: an in-use source needs its retrieval or generation date")
        if s.get("license") == "CHECK_SOURCE":
            problems.append(f"{sid}: an in-use source needs its licence or terms confirmed")
        if not s.get("transformation_script"):
            problems.append(f"{sid}: missing transformation_script")
        paths = s.get("paths") or []
        if not paths:
            problems.append(f"{sid}: an in-use source must list its files")
        elif missing := [p for p in paths if not (root / p).exists()]:
            problems.append(f"{sid}: files not found: {', '.join(missing)}")
        elif not s.get("checksum_sha256"):
            problems.append(f"{sid}: missing checksum_sha256")
        elif tree_sha256(root, paths) != s["checksum_sha256"]:
            problems.append(f"{sid}: checksum does not match the files on disk")
    elif s.get("status") == "REGISTERED":
        if not str(s.get("url", "")).startswith("https://"):
            problems.append(f"{sid}: a registered external source needs an https URL")
        if s.get("paths") or s.get("checksum_sha256"):
            problems.append(f"{sid}: a registered source is not downloaded, so it has no files or checksum")
    return problems


def validate_registry(registry: dict, root: Path | None = None) -> dict:
    root = root or settings.data_dir.parent
    sources = registry.get("sources") or []
    ids = [s.get("id") for s in sources]
    problems = [f"duplicate id {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    results = []
    for s in sources:
        p = validate_source(s, root)
        problems.extend(p)
        results.append({**s, "valid": not p, "problems": p})
    return {"schema_version": registry.get("schema_version"), "sources": results, "problems": problems,
            "valid": not problems}


def load_registry(path: Path | None = None) -> dict:
    return validate_registry(json.loads((path or registry_path()).read_text(encoding="utf-8")))


def stamp_checksums(path: Path | None = None, root: Path | None = None) -> dict:
    """Recompute checksum_sha256 for every in-use source (run after regenerating data)."""
    path, root = path or registry_path(), root or settings.data_dir.parent
    registry = json.loads(path.read_text(encoding="utf-8"))
    for s in registry["sources"]:
        if s.get("status") == "IN_USE" and s.get("paths"):
            s["checksum_sha256"] = tree_sha256(root, s["paths"])
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return registry


# ---------------------------------------------------------------- RAG ingestion manifest
def _runs(db: Session) -> dict[int, PolicyIngestion]:
    """The latest successful extraction run per policy version."""
    out: dict[int, PolicyIngestion] = {}
    for r in db.query(PolicyIngestion).filter_by(status="READY").order_by(PolicyIngestion.id).all():
        if r.policy_version_id is not None:
            out[r.policy_version_id] = r
    return out


def _missing(c: PolicyClause, v: PolicyVersion, run: PolicyIngestion | None) -> list[str]:
    checks = {"source file": v.source_file, "page": c.page and c.page >= 1, "section": c.section,
              "clause": c.clause_ref, "text": c.text, "extraction run": run}
    return [k for k, ok in checks.items() if not ok]


def indexable(db: Session) -> tuple[list[PolicyClause], list[dict]]:
    """Clauses with complete provenance, and the ones rejected with the reason."""
    runs = _runs(db)
    keep, rejected = [], []
    for c in db.query(PolicyClause).order_by(PolicyClause.id).all():
        if missing := _missing(c, c.version, runs.get(c.version_id)):
            rejected.append({"clause_id": c.id, "product_code": c.version.policy.product_code,
                             "version": c.version.version, "clause_ref": c.clause_ref, "missing": missing})
        else:
            keep.append(c)
    return keep, rejected


def _ref_key(ref: str) -> list:
    return [(0, int(x), "") if x.isdigit() else (1, 0, x) for x in ref.split(".")]


def rag_manifest(db: Session) -> dict:
    """Every indexed chunk resolved to source file, document/version, page, section/clause and extraction run.
    Deterministic for the same data, so a fresh build can be compared with the committed copy."""
    runs = _runs(db)
    keep, rejected = indexable(db)
    versions: dict[int, dict] = {}
    chunks = []
    for c in keep:
        v, run = c.version, runs[c.version_id]
        key = f"{v.policy.product_code}@{v.version}"
        versions.setdefault(v.id, {"document": key, "source_file": v.source_file, "source_sha256": run.sha256,
                                   "file_type": run.file_type, "extraction_run": run.id, "pages": run.pages,
                                   "effective_from": v.effective_from.isoformat(), "effective_to": v.effective_to.isoformat(),
                                   "chunks": 0})
        versions[v.id]["chunks"] += 1
        chunks.append({"chunk_id": f"{key}#{c.clause_ref}", "document": key, "source_file": v.source_file,
                       "page": c.page, "section": c.section, "clause_ref": c.clause_ref, "title": c.title,
                       "extraction_run": run.id, "text_sha256": hashlib.sha256(c.text.encode()).hexdigest()})
    return {"manifest_version": "1.0", "indexed_chunks": len(chunks), "rejected_chunks": len(rejected),
            "documents": sorted(versions.values(), key=lambda d: d["document"]),
            "chunks": sorted(chunks, key=lambda c: (c["document"], _ref_key(c["clause_ref"]))),
            "rejected": rejected}
