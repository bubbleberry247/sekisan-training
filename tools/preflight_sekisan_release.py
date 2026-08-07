#!/usr/bin/env python3
"""Read-only release gate for the Sekisan question bank and question images."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_DIR / "data" / "sekisan_all_final.csv"
DEFAULT_FIXTURE = REPO_DIR / "data" / "sekisan_question_corrections_20260807.json"
IMAGE_DIR = REPO_DIR / "images" / "sekisan"
SEKISAN_CONFIG = REPO_DIR / "src" / "sekisanConfig.gs"
IMAGE_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "bubbleberry247/sekisan-training/main/images/sekisan/"
)
GITHUB_CONTENTS_URL = (
    "https://api.github.com/repos/bubbleberry247/sekisan-training/"
    "contents/images/sekisan?ref=main"
)
REQUIRED_CORRECTION_FIELDS = {
    "stem",
    "choiceA",
    "choiceB",
    "choiceC",
    "choiceD",
    "correct",
    "imageUrl",
}
EXPECTED_CORRECTION_COUNT = 37
EXPECTED_IMAGE_COUNT = 114


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Skip Git tracking and GitHub publication checks.",
    )
    return parser.parse_args()


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def expected_image_name(qid: str) -> str:
    match = re.fullmatch(r"((?:H|R)\d+)sekisan-(\d{3})", qid)
    if not match:
        return ""
    return f"sekisan_{match.group(1)}_{match.group(2)}.png"


def tracked_image_names() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "--", "images/sekisan/*.png"],
        cwd=REPO_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    return {Path(line.strip()).name for line in result.stdout.splitlines() if line.strip()}


def published_image_names() -> set[str]:
    request = urllib.request.Request(
        GITHUB_CONTENTS_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "sekisan-preflight"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return {
        str(item.get("name", ""))
        for item in payload
        if re.fullmatch(r"sekisan_(?:H|R)\d+_\d{3}\.png", str(item.get("name", "")))
    }


def main() -> int:
    args = parse_args()
    issues: list[str] = []
    headers, rows = load_csv(args.csv)
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    corrections: dict[str, dict[str, str]] = fixture.get("corrections", {})
    excluded = set(fixture.get("excludedVersionDifferences", {}))
    presentation = fixture.get("presentationAudit", {})
    presentation_questions = presentation.get("questions", {})
    required_stem_fragments = presentation.get("requiredStemFragments", {})
    context_images = presentation.get("contextImages", {})

    required_csv_fields = {"qId", "choiceImageUrl", *REQUIRED_CORRECTION_FIELDS}
    missing_headers = sorted(required_csv_fields - set(headers))
    if missing_headers:
        issues.append("CSV missing headers: " + ", ".join(missing_headers))

    qids = [row.get("qId", "") for row in rows]
    row_map = {row.get("qId", ""): row for row in rows}
    if len(rows) != 650 or len(row_map) != 650:
        issues.append(f"QuestionBank cardinality must be 650 unique rows: rows={len(rows)}, unique={len(row_map)}")
    if len(corrections) != EXPECTED_CORRECTION_COUNT:
        issues.append(
            f"Verified correction fixture must contain {EXPECTED_CORRECTION_COUNT} rows: {len(corrections)}"
        )
    if set(presentation_questions) != set(corrections):
        missing = sorted(set(corrections) - set(presentation_questions))
        extra = sorted(set(presentation_questions) - set(corrections))
        issues.append(f"Presentation audit must cover every correction: missing={missing}, extra={extra}")
    overlap = sorted(set(corrections) & excluded)
    if overlap:
        issues.append("Version-difference exclusions must not be corrected: " + ", ".join(overlap))

    for qid, correction in corrections.items():
        if qid not in row_map:
            issues.append(f"Fixture qId missing from CSV: {qid}")
            continue
        missing = sorted(REQUIRED_CORRECTION_FIELDS - set(correction))
        extra = sorted(set(correction) - REQUIRED_CORRECTION_FIELDS)
        if missing:
            issues.append(f"{qid}: fixture missing fields {missing}")
        if extra:
            issues.append(f"{qid}: fixture has unsupported fields {extra}")
        for field in ("stem", "choiceA", "choiceB", "choiceC", "choiceD", "correct"):
            if not str(correction.get(field, "")).strip():
                issues.append(f"{qid}: empty {field}")
        if not re.fullmatch(r"[A-D](?:,[A-D])?", str(correction.get("correct", ""))):
            issues.append(f"{qid}: invalid correct value {correction.get('correct')!r}")
        for field in sorted(REQUIRED_CORRECTION_FIELDS):
            expected = str(correction.get(field, ""))
            actual = str(row_map[qid].get(field, ""))
            if actual != expected:
                issues.append(f"{qid}: CSV {field} does not match verified fixture")

        audit = presentation_questions.get(qid, {})
        question_mode = audit.get("question")
        choice_mode = audit.get("choices")
        if question_mode not in {"text", "questionImage"}:
            issues.append(f"{qid}: invalid presentation question mode {question_mode!r}")
        if choice_mode not in {"text", "choiceImage"}:
            issues.append(f"{qid}: invalid presentation choice mode {choice_mode!r}")
        has_question_image = bool(str(correction.get("imageUrl", "")).strip())
        if (question_mode == "questionImage") != has_question_image:
            issues.append(f"{qid}: presentation question mode and imageUrl disagree")
        has_choice_image = bool(str(row_map[qid].get("choiceImageUrl", "")).strip())
        if (choice_mode == "choiceImage") != has_choice_image:
            issues.append(f"{qid}: presentation choice mode and choiceImageUrl disagree")

    for qid, fragments in required_stem_fragments.items():
        if qid not in corrections:
            issues.append(f"Presentation stem fragments reference unknown qId: {qid}")
            continue
        if not isinstance(fragments, list) or not fragments:
            issues.append(f"{qid}: requiredStemFragments must be a non-empty list")
            continue
        stem = str(corrections[qid].get("stem", ""))
        for fragment in fragments:
            if str(fragment) not in stem:
                issues.append(f"{qid}: required stem context missing: {fragment!r}")

    for qid, image_spec in context_images.items():
        correction = corrections.get(qid)
        if correction is None:
            issues.append(f"Context image references unknown qId: {qid}")
            continue
        filename = str(image_spec.get("file", ""))
        if not filename or not str(correction.get("imageUrl", "")).endswith("/" + filename):
            issues.append(f"{qid}: context image filename and correction imageUrl disagree")
            continue
        path = IMAGE_DIR / filename
        if not path.is_file():
            issues.append(f"{qid}: context image missing: {filename}")
            continue
        payload = path.read_bytes()
        actual_sha = hashlib.sha256(payload).hexdigest().upper()
        expected_sha = str(image_spec.get("sha256", "")).upper()
        if actual_sha != expected_sha:
            issues.append(f"{qid}: context image SHA-256 mismatch")
        if len(payload) < 24 or payload[:8] != b"\x89PNG\r\n\x1a\n":
            issues.append(f"{qid}: context image is not a valid PNG")
            continue
        width, height = struct.unpack(">II", payload[16:24])
        if width != int(image_spec.get("width", -1)) or height != int(image_spec.get("height", -1)):
            issues.append(
                f"{qid}: context image dimensions mismatch: expected="
                f"{image_spec.get('width')}x{image_spec.get('height')} actual={width}x{height}"
            )

    duplicate_choice_qids: list[str] = []
    placeholder_choice_qids: list[str] = []
    for qid in qids:
        row = row_map[qid]
        choices = [str(row.get(f"choice{key}", "")).strip() for key in "ABCD"]
        if len(set(choices)) != 4:
            duplicate_choice_qids.append(qid)
        if choices == ["1", "2", "3", "4"]:
            placeholder_choice_qids.append(qid)
    if duplicate_choice_qids:
        issues.append("Duplicate choices remain: " + ", ".join(duplicate_choice_qids))
    if placeholder_choice_qids:
        issues.append("1/2/3/4 placeholder choices remain: " + ", ".join(placeholder_choice_qids))

    image_qids = {
        qid
        for qid in qids
        if str(row_map[qid].get("imageUrl", "")).strip()
    }
    if len(image_qids) != EXPECTED_IMAGE_COUNT:
        issues.append(f"Expected {EXPECTED_IMAGE_COUNT} image rows, found {len(image_qids)}")

    config_source = SEKISAN_CONFIG.read_text(encoding="utf-8")
    count_match = re.search(r"SEKISAN_EXPECTED_IMAGE_COUNT_\s*=\s*(\d+)\s*;", config_source)
    if not count_match:
        issues.append("src/sekisanConfig.gs does not declare SEKISAN_EXPECTED_IMAGE_COUNT_")
    elif int(count_match.group(1)) != EXPECTED_IMAGE_COUNT:
        issues.append(
            "src/sekisanConfig.gs image count does not match release preflight: "
            f"config={count_match.group(1)}, preflight={EXPECTED_IMAGE_COUNT}"
        )

    expected_names = {expected_image_name(qid) for qid in image_qids}
    expected_names.discard("")
    if len(expected_names) != len(image_qids):
        issues.append("Image qId-to-filename mapping is not one-to-one")

    missing_local: list[str] = []
    invalid_png: list[str] = []
    for name in sorted(expected_names):
        path = IMAGE_DIR / name
        if not path.is_file() or path.stat().st_size == 0:
            missing_local.append(name)
            continue
        if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            invalid_png.append(name)
    if missing_local:
        issues.append("Missing local images: " + ", ".join(missing_local))
    if invalid_png:
        issues.append("Invalid PNG files: " + ", ".join(invalid_png))

    canonical_urls = {IMAGE_BASE_URL + name for name in expected_names}
    if len(canonical_urls) != EXPECTED_IMAGE_COUNT:
        issues.append(f"Canonical absolute image URL count is {len(canonical_urls)}, expected {EXPECTED_IMAGE_COUNT}")

    missing_tracked: list[str] = []
    missing_published: list[str] = []
    if not args.local_only:
        tracked = tracked_image_names()
        missing_tracked = sorted(expected_names - tracked)
        if missing_tracked:
            issues.append("Images not tracked by Git: " + ", ".join(missing_tracked))
        try:
            published = published_image_names()
            missing_published = sorted(expected_names - published)
            if missing_published:
                issues.append("Images not published on GitHub main: " + ", ".join(missing_published))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            issues.append(f"GitHub image listing failed: {exc}")

    report = {
        "ok": not issues,
        "questionRows": len(rows),
        "fixtureCorrections": len(corrections),
        "presentationAuditQuestions": len(presentation_questions),
        "verifiedContextImages": len(context_images),
        "excludedVersionDifferences": sorted(excluded),
        "imageRows": len(image_qids),
        "localImages": len(expected_names) - len(missing_local),
        "missingTrackedImages": missing_tracked,
        "missingPublishedImages": missing_published,
        "issues": issues,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
