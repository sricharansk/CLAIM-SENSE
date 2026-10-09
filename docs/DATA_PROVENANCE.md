# Data provenance — Claim Sense

Claim Sense runs on synthetic data only. This page explains where every source comes from and how the build checks it. The register itself is `data/source_registry.json`. The live, validated view is the **Data sources** screen (`GET /api/v1/datasets`).

## Source registry (blueprint Data Prompt A)

Each entry records:

- id, name and publisher;
- source type (`synthetic`, `regulatory`, `statistical`, `benchmark`) and data type;
- whether it holds claim-level rows (`null` until a registered source is downloaded and checked);
- URL, publication date, retrieval or generation date, and data period;
- licence or terms, and intended use;
- status, files, transformation script and SHA-256 checksum.

`backend/app/provenance.py` rejects an entry when:

- a required field is missing, or a date is not `YYYY`, `YYYY-MM` or `YYYY-MM-DD`;
- an **in-use** source has no retrieval date, no transformation script, no files, an unconfirmed licence (`CHECK_SOURCE`), or a checksum that does not match its files on disk;
- a **registered** source has no `https` URL, or claims files or a checksum although it was not downloaded;
- two entries share an id.

The checksum of a source spanning several files or folders is a SHA-256 over each file's relative path and SHA-256, so adding, removing or editing any file changes it. `.gitattributes` stores `data/**` byte for byte, so checksums match on every platform.

| Status | Sources | What it means |
|---|---|---|
| IN_USE | 5 synthetic sources: policy corpus, PDF ingestion demo, golden claim packets and the 42-claim demo book, claims portfolio, evaluation set | Generated or written in this repository; checksums verified on every request |
| REGISTERED | 9 public sources: three IRDAI master circulars, IRDAI handbook 2024-25, APRA NCPD, CMS TiC PUF PY2026, Figshare and two Zenodo benchmarks | Dates and URLs come from the blueprint's verified register. They are not downloaded in this build, and most licences are still `CHECK_SOURCE` |

No public dataset is described as live 2026 claim-level data. APRA NCPD is a 2026 publication of data through December 2024.

## RAG ingestion manifest (blueprint Data Prompt G)

`GET /api/v1/knowledge-base/manifest` lists every indexed policy chunk with:

- chunk id (`PRODUCT@VERSION#CLAUSE`);
- source file and the SHA-256 of the uploaded file;
- page, section and clause;
- the extraction run (the `policy_ingestions` record that produced it);
- a SHA-256 of the chunk text.

The retrieval index only accepts a chunk whose source file, page, section, clause, text and successful extraction run all resolve. Anything else is kept out of the index and listed under `rejected`. Databases created before ingestion runs were recorded get a run backfilled from the same source file at start-up, marked `seed (backfill)`.

`reports/rag_manifest.json` is the manifest built from a fresh database seeded from `data/`. `python scripts/provenance.py --check` rebuilds it and fails if it differs from the committed copy, if any chunk is rejected, or if the registry has a problem. CI runs this check.

## After changing data

```bash
python data/synthetic/generate.py          # if regenerating synthetic data
python scripts/provenance.py --write       # re-stamp checksums and rewrite the manifest
python scripts/evaluate.py                 # re-run the golden evaluation
```
