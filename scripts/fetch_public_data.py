#!/usr/bin/env python3
"""Fetch the CAS Loss Reserving Database (Schedule P) and write industry benchmarks by line of business.

Usage:
  python scripts/fetch_public_data.py            # download, verify, aggregate, write data/public/cas_schedule_p/
  python scripts/fetch_public_data.py --raw-dir data/raw/cas   # also keep the raw CSV (data/raw/ is not committed)

Source: the Casualty Actuarial Society's Loss Reserving Database, compiled for the CAS by S&P Global Market
Intelligence from US NAIC Schedule P (accident years 1998-2007, ten development years, six lines; amounts in
USD thousands). https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p

The CAS web site is not reachable from every build environment, so the script takes the same file as
redistributed in the `chainladder` package's source distribution on PyPI (MPL-2.0), pinned by SHA-256. Only the
one CSV is read from the archive (nothing is extracted to disk or executed). The repository commits only the
aggregates below, never the company-level rows.

Pipeline (blueprint Part 9): download -> SHA-256 check -> parse -> schema check -> aggregate -> quality report.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import tarfile
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "public" / "cas_schedule_p" / "benchmark.json"
SDIST_URL = "https://files.pythonhosted.org/packages/source/c/chainladder/chainladder-0.10.1.tar.gz"
SDIST_SHA256 = "5346c942dcaa9cd4b5118c0fcb2db298de615eb066cde7a31f18b439c0e1fc15"
MEMBER = "chainladder-0.10.1/chainladder/utils/data/clrd2025.csv"
COLUMNS = ["GRCODE", "GRNAME", "AccidentYear", "DevelopmentYear", "DevelopmentLag", "IncurredLosses", "CumPaidLoss",
           "BulkLoss", "EarnedPremDIR", "EarnedPremCeded", "EarnedPremNet", "Single", "PostedReserves2007", "LOB"]
LINES = {"ppauto": "Private passenger auto liability", "comauto": "Commercial auto liability",
         "wkcomp": "Workers' compensation", "medmal": "Medical malpractice (occurrence)",
         "othliab": "Other liability (occurrence)", "prodliab": "Products liability (occurrence)"}
LAGS = range(1, 11)


def download() -> bytes:
    req = urllib.request.Request(SDIST_URL, headers={"User-Agent": "claim-sense-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 (fixed https URL)
        blob = r.read()
    got = hashlib.sha256(blob).hexdigest()
    if got != SDIST_SHA256:
        sys.exit(f"checksum mismatch for {SDIST_URL}: expected {SDIST_SHA256}, got {got}")
    return blob


def read_csv(blob: bytes) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        member = tar.getmember(MEMBER)
        if not member.isfile():
            sys.exit(f"{MEMBER} is not a regular file")
        return tar.extractfile(member).read()


def aggregate(raw: bytes) -> dict:
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
    if not rows or list(rows[0]) != COLUMNS:
        sys.exit(f"unexpected columns: {list(rows[0]) if rows else 'empty file'}")
    problems: list[str] = []
    # (line, accident year, lag) -> sums; (line, accident year) -> net earned premium (same on every lag row)
    paid, incurred = defaultdict(float), defaultdict(float)
    premium: dict[tuple, float] = {}
    companies: dict[str, set] = defaultdict(set)
    for r in rows:
        line, ay, lag = r["LOB"], int(r["AccidentYear"]), int(r["DevelopmentLag"])
        if line not in LINES or lag not in LAGS or not 1998 <= ay <= 2007:
            problems.append(f"out-of-range row: {line} {ay} {lag}")
            continue
        companies[line].add(r["GRCODE"])
        paid[line, ay, lag] += float(r["CumPaidLoss"])
        incurred[line, ay, lag] += float(r["IncurredLosses"])
        if lag == 1:
            premium[line, r["GRCODE"], ay] = float(r["EarnedPremNet"])
    out = {}
    for line, label in LINES.items():
        years, ep_total, inc_total = [], 0.0, 0.0
        for ay in range(1998, 2008):
            ep = sum(v for (ln, _, y), v in premium.items() if ln == line and y == ay)
            ult = incurred[line, ay, 10]
            ep_total += ep
            inc_total += ult
            years.append({"accident_year": ay, "net_earned_premium": round(ep), "incurred_at_10_years": round(ult),
                          "paid_at_10_years": round(paid[line, ay, 10]),
                          "loss_ratio": round(ult / ep, 3) if ep > 0 else None})
        base = sum(paid[line, ay, 10] for ay in range(1998, 2008))
        pattern = [{"lag_years": lag, "percent_paid": round(100 * sum(paid[line, ay, lag] for ay in range(1998, 2008)) / base, 1)}
                   for lag in LAGS] if base else []
        out[line] = {"label": label, "companies": len(companies[line]),
                     "net_earned_premium": round(ep_total), "incurred_at_10_years": round(inc_total),
                     "loss_ratio": round(inc_total / ep_total, 3) if ep_total else None,
                     "paid_development": pattern, "accident_years": years}
    return {"rows": len(rows), "problems": problems, "lines": out}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw-dir", type=Path, help="also write the raw CSV here (keep it out of git)")
    args = ap.parse_args()
    blob = download()
    raw = read_csv(blob)
    agg = aggregate(raw)
    if agg["problems"]:
        sys.exit("quality check failed:\n" + "\n".join(agg["problems"][:20]))
    if args.raw_dir:
        args.raw_dir.mkdir(parents=True, exist_ok=True)
        (args.raw_dir / "clrd2025.csv").write_bytes(raw)
    report = {
        "dataset_id": "cas-schedule-p-1998-2007",
        "source": {
            "name": "CAS Loss Reserving Database (NAIC Schedule P), accident years 1998-2007",
            "publisher": "Casualty Actuarial Society; compiled for the CAS by S&P Global Market Intelligence",
            "url": "https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p",
            "retrieved_from": SDIST_URL, "archive_sha256": SDIST_SHA256, "file": MEMBER.rsplit("/", 1)[-1],
            "file_sha256": hashlib.sha256(raw).hexdigest(), "retrieval_date": date.today().isoformat(),
            "units": "USD thousands", "transformation_script": "scripts/fetch_public_data.py",
        },
        "definitions": {
            "loss_ratio": "incurred losses (case + bulk reserves + paid) at development year 10 / net earned premium",
            "paid_development": "industry cumulative paid at each development year as a percentage of paid at year 10, "
                                "all accident years pooled",
            "companies": "distinct NAIC group or company codes reporting the line",
        },
        "rows_read": agg["rows"],
        "lines": agg["lines"],
        "note": "US commercial and personal lines industry data, used as an external benchmark for how claims develop. "
                "It is not used in any claim decision and the synthetic Claim Sense book is not calibrated to it.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"read {agg['rows']} rows, 0 problems; wrote {OUT.relative_to(ROOT)}")
    for line, v in agg["lines"].items():
        print(f"  {line:9} companies {v['companies']:4}  loss ratio {v['loss_ratio']:.3f}  "
              f"paid at year 1/3/5: {v['paid_development'][0]['percent_paid']}% / "
              f"{v['paid_development'][2]['percent_paid']}% / {v['paid_development'][4]['percent_paid']}%")


if __name__ == "__main__":
    main()
