#!/usr/bin/env python3
"""Validate data provenance and the RAG ingestion manifest.

Usage:
  python scripts/provenance.py --check   # CI: registry valid, checksums match, manifest reproducible
  python scripts/provenance.py --write   # after regenerating data: re-stamp checksums, rewrite the manifest

The manifest is built from a fresh, isolated database seeded from data/, so the same data always gives the same
manifest. Every indexed chunk must resolve to source file, document/version, page, section/clause and extraction
run; a chunk without provenance is rejected and fails the check.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports" / "rag_manifest.json"


def build_manifest() -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="claimsense-manifest-"))
    os.environ.update(DATABASE_URL=f"sqlite:///{tmp / 'manifest.db'}", CLAIMSENSE_STORAGE_DIR=str(tmp / "storage"))
    os.environ.pop("ANTHROPIC_API_KEY", None)
    sys.path.insert(0, str(ROOT / "backend"))
    from app import provenance
    from app.db import Base, SessionLocal, engine
    from app.seed import seed

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db, analyze=False)
        return provenance.rag_manifest(db)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = ap.parse_args()
    sys.path.insert(0, str(ROOT / "backend"))
    from app import provenance

    if args.write:
        provenance.stamp_checksums()
    registry = provenance.load_registry()
    in_use = sum(s["status"] == "IN_USE" for s in registry["sources"])
    print(f"source registry: {len(registry['sources'])} sources ({in_use} in use), {len(registry['problems'])} problems")
    for p in registry["problems"]:
        print(f"  FAIL {p}")

    manifest = build_manifest()
    print(f"rag manifest: {manifest['indexed_chunks']} chunks from {len(manifest['documents'])} documents, "
          f"{manifest['rejected_chunks']} rejected")
    for r in manifest["rejected"]:
        print(f"  FAIL chunk {r['product_code']}@{r['version']}#{r['clause_ref']} missing {', '.join(r['missing'])}")
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    ok = registry["valid"] and not manifest["rejected"]
    if args.write:
        MANIFEST.write_text(text, encoding="utf-8")
        print(f"wrote {MANIFEST.relative_to(ROOT)}")
    elif not MANIFEST.exists() or MANIFEST.read_text(encoding="utf-8") != text:
        print(f"  FAIL {MANIFEST.relative_to(ROOT)} is out of date; run python scripts/provenance.py --write")
        ok = False
    print("provenance check passed" if ok else "provenance check FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
