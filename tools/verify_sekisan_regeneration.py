#!/usr/bin/env python3
"""Fail unless regenerated Sekisan CSV matches the tracked canonical CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CANONICAL = REPO_DIR / "data" / "sekisan_all_final.csv"
DEFAULT_IGNORED_FIELDS = {"updatedAt"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--canonical", type=Path, default=DEFAULT_CANONICAL)
    return parser.parse_args()


def read_csv(path: Path) -> tuple[list[str], dict[str, dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = list(reader)
    row_map = {row.get("qId", ""): row for row in rows}
    if len(row_map) != len(rows):
        raise ValueError(f"Duplicate qId in {path}")
    return headers, row_map


def main() -> int:
    args = parse_args()
    canonical_headers, canonical = read_csv(args.canonical)
    candidate_headers, candidate = read_csv(args.candidate)
    issues: list[dict[str, str]] = []

    if canonical_headers != candidate_headers:
        issues.append({"qId": "", "field": "headers", "expected": str(canonical_headers), "actual": str(candidate_headers)})
    for qid in sorted(set(canonical) | set(candidate)):
        if qid not in canonical:
            issues.append({"qId": qid, "field": "row", "expected": "missing", "actual": "present"})
            continue
        if qid not in candidate:
            issues.append({"qId": qid, "field": "row", "expected": "present", "actual": "missing"})
            continue
        for field in canonical_headers:
            if field in DEFAULT_IGNORED_FIELDS:
                continue
            expected = str(canonical[qid].get(field, ""))
            actual = str(candidate[qid].get(field, ""))
            if expected != actual:
                issues.append({"qId": qid, "field": field, "expected": expected, "actual": actual})

    report = {
        "ok": not issues,
        "canonicalRows": len(canonical),
        "candidateRows": len(candidate),
        "ignoredFields": sorted(DEFAULT_IGNORED_FIELDS),
        "differenceCount": len(issues),
        "differences": issues[:50],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
