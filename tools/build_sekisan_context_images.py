#!/usr/bin/env python3
"""Render the two verified context tables missing from the Sekisan UI.

The crop coordinates are tied to the exam-time original PDFs recorded in
``sekisan_question_corrections_20260807.json``.  This script refuses to render
from a later replacement PDF with a different SHA-256.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import fitz
from PIL import Image


REPO_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_DIR / "images" / "sekisan"
SCALE = 4.0

# Pixel crops after rendering the full landscape page at SCALE=4.0.  Keeping
# these as explicit audited crops prevents an automatic figure detector from
# accidentally taking the answer/explanation table on the right half.
SPECS = {
    "H25sekisan-017": {
        "pdf": "sekisan_H25_1ji.pdf",
        "sha256": "F45A0DFA0A7F7F0941E1C04EAF3B982E4C5501AD7923A699A817B1C04417419E",
        "page": 17,
        "crop": (245, 575, 985, 1685),
        "output": "sekisan_H25_017.png",
    },
    "H28sekisan-020": {
        "pdf": "sekisan_H28_1ji.pdf",
        "sha256": "B61F35226D4E6F49F2F52C5B7D5092C0E1CC2802D14D0D1C9A82068BF3F8CBA8",
        "page": 20,
        "crop": (350, 520, 1180, 1160),
        "output": "sekisan_H28_020.png",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def render(pdf_path: Path, page_number: int, crop: tuple[int, int, int, int]) -> Image.Image:
    document = fitz.open(pdf_path)
    try:
        page = document[page_number - 1]
        pixmap = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
        page_image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        image = page_image.crop(crop)
        if image.width < 500 or image.height < 400:
            raise ValueError(f"Context crop is unexpectedly small: {image.size}")
        return image
    finally:
        document.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for qid, spec in SPECS.items():
        pdf_path = args.pdf_root / str(spec["pdf"])
        if not pdf_path.is_file():
            raise SystemExit(f"{qid}: source PDF not found: {pdf_path}")
        actual_sha = sha256(pdf_path)
        if actual_sha != spec["sha256"]:
            raise SystemExit(
                f"{qid}: source PDF SHA-256 mismatch: expected={spec['sha256']} actual={actual_sha}"
            )
        image = render(pdf_path, int(spec["page"]), tuple(spec["crop"]))
        output_path = args.output_dir / str(spec["output"])
        image.save(output_path, format="PNG", optimize=True)
        print(f"{qid}: {output_path} {image.width}x{image.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
