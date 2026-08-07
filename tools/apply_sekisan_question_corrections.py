#!/usr/bin/env python3
"""Apply the verified Sekisan correction fixture to a CSV without touching Sheets."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_DIR / "data" / "sekisan_all_final.csv"
DEFAULT_FIXTURE = REPO_DIR / "data" / "sekisan_question_corrections_20260807.json"
FIELDS = ["stem", "choiceA", "choiceB", "choiceC", "choiceD", "correct", "imageUrl"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output", type=Path, help="Write the corrected CSV to this new path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output and args.output.resolve() == args.input.resolve():
        raise SystemExit("Refusing to overwrite the input CSV; choose a separate --output path")

    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    corrections: dict[str, dict[str, str]] = fixture["corrections"]
    with args.input.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = list(reader)

    missing_headers = [field for field in ["qId", *FIELDS] if field not in headers]
    if missing_headers:
        raise SystemExit("Missing CSV headers: " + ", ".join(missing_headers))

    seen: set[str] = set()
    changed_fields = 0
    for row in rows:
        qid = row["qId"]
        correction = corrections.get(qid)
        if correction is None:
            continue
        seen.add(qid)
        for field in FIELDS:
            value = str(correction[field])
            if row.get(field, "") != value:
                changed_fields += 1
                row[field] = value

    missing_qids = sorted(set(corrections) - seen)
    if missing_qids:
        raise SystemExit("Fixture qIds missing from CSV: " + ", ".join(missing_qids))

    print(
        json.dumps(
            {
                "input": str(args.input),
                "fixtureRows": len(corrections),
                "changedFields": changed_fields,
                "output": str(args.output) if args.output else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
