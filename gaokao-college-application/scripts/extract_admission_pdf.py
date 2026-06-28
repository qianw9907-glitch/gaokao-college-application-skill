#!/usr/bin/env python3
"""Extract admission-plan text snippets from official Gaokao PDFs.

The script is intentionally conservative:
- Prefer embedded PDF text when available.
- Use OCR only when --ocr is passed and local tools are installed.
- Emit snippets or review rows instead of pretending to parse every province's
  PDF layout perfectly.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Snippet:
    page: int
    target: str
    text: str
    confidence: str


@dataclass
class AdmissionRow:
    page: int
    target: str
    confidence: str
    school_name: str
    school_code: str
    group_code: str
    subject_requirement: str
    admission_type: str
    major_name: str
    plan_count: str
    tuition: str
    campus: str
    raw_text: str
    needs_review: str


ROW_FIELDS = [
    "page",
    "target",
    "confidence",
    "school_name",
    "school_code",
    "group_code",
    "subject_requirement",
    "admission_type",
    "major_name",
    "plan_count",
    "tuition",
    "campus",
    "raw_text",
    "needs_review",
]


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout


def extract_with_pymupdf(pdf: Path, pages: set[int] | None) -> list[tuple[int, str]]:
    try:
        import fitz  # type: ignore
    except Exception:
        return []

    output: list[tuple[int, str]] = []
    doc = fitz.open(pdf)
    for idx, page in enumerate(doc, start=1):
        if pages and idx not in pages:
            continue
        text = page.get_text("text").strip()
        output.append((idx, text))
    return output


def extract_with_pdfplumber(pdf: Path, pages: set[int] | None) -> list[tuple[int, str]]:
    try:
        import pdfplumber  # type: ignore
    except Exception:
        return []

    output: list[tuple[int, str]] = []
    with pdfplumber.open(pdf) as doc:
        for idx, page in enumerate(doc.pages, start=1):
            if pages and idx not in pages:
                continue
            text = page.extract_text(layout=True) or ""
            output.append((idx, text.strip()))
    return output


def extract_with_pdftotext(pdf: Path, pages: set[int] | None) -> list[tuple[int, str]]:
    if not shutil.which("pdftotext"):
        return []

    if pages:
        output: list[tuple[int, str]] = []
        for page in sorted(pages):
            text = run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"])
            output.append((page, text.strip()))
        return output

    text = run(["pdftotext", "-layout", str(pdf), "-"])
    chunks = text.split("\f")
    return [(idx, chunk.strip()) for idx, chunk in enumerate(chunks, start=1)]


def extract_with_ocr(pdf: Path, pages: set[int] | None, lang: str) -> list[tuple[int, str]]:
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        raise SystemExit(
            "OCR requires local tools: pdftoppm and tesseract. "
            "Install them or run without --ocr to use embedded text only."
        )

    output: list[tuple[int, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "page"
        base = ["pdftoppm", "-r", "220", "-png"]
        if pages:
            for page in sorted(pages):
                run(base + ["-f", str(page), "-l", str(page), str(pdf), str(prefix)])
                image = next(Path(tmp).glob("page-*.png"))
                text = run(["tesseract", str(image), "stdout", "-l", lang, "--psm", "6"])
                output.append((page, text.strip()))
                image.unlink(missing_ok=True)
        else:
            run(base + [str(pdf), str(prefix)])
            for idx, image in enumerate(sorted(Path(tmp).glob("page-*.png")), start=1):
                text = run(["tesseract", str(image), "stdout", "-l", lang, "--psm", "6"])
                output.append((idx, text.strip()))
    return output


def parse_pages(raw: str | None) -> set[int] | None:
    if not raw:
        return None
    pages: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(part))
    return pages


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def find_snippets(
    pages: list[tuple[int, str]],
    targets: list[str],
    context_chars: int,
    confidence: str,
) -> list[Snippet]:
    snippets: list[Snippet] = []
    for page_num, text in pages:
        if not text:
            continue
        compact = normalize(text)
        for target in targets:
            pattern = re.escape(target)
            for match in re.finditer(pattern, compact, flags=re.IGNORECASE):
                start = max(0, match.start() - context_chars)
                end = min(len(compact), match.end() + context_chars)
                snippets.append(
                    Snippet(
                        page=page_num,
                        target=target,
                        text=compact[start:end],
                        confidence=confidence,
                    )
                )
    return snippets


def find_review_rows(
    pages: list[tuple[int, str]],
    targets: list[str],
    line_context: int,
    confidence: str,
) -> list[AdmissionRow]:
    rows: list[AdmissionRow] = []
    seen: set[tuple[int, str, str]] = set()
    for page_num, text in pages:
        lines = [clean_line(line) for line in text.splitlines() if clean_line(line)]
        for idx, line in enumerate(lines):
            matched_targets = [target for target in targets if re.search(re.escape(target), line, re.IGNORECASE)]
            if not matched_targets:
                continue
            start = max(0, idx - line_context)
            end = min(len(lines), idx + line_context + 1)
            for target in matched_targets:
                for candidate in lines[start:end]:
                    key = (page_num, target, candidate)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(row_from_text(page_num, target, candidate, confidence))
    return rows


def first_match(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def row_from_text(page: int, target: str, text: str, confidence: str) -> AdmissionRow:
    school_name = first_match(
        [
            r"([\u4e00-\u9fffA-Za-z（）()·]{2,40}(?:大学|学院|学校))",
            r"([\u4e00-\u9fffA-Za-z（）()·]{2,40}(?:职业技术大学|高等专科学校))",
        ],
        text,
    )
    if not school_name and any(keyword in text for keyword in ["大学", "学院", "学校"]):
        school_name = target if not re.fullmatch(r"[A-Za-z]?\d{2,6}", target) else ""

    group_code = first_match(
        [
            r"([A-Z]?\d{2,3})\s*组",
            r"专业组\s*([A-Z]?\d{2,3})",
            r"组号[:：]?\s*([A-Z]?\d{2,3})",
        ],
        text,
    )
    if not group_code and re.fullmatch(r"[A-Z]?\d{2,3}", target):
        group_code = target

    school_code = first_match(
        [
            r"院校(?:代号|代码)[:：]?\s*([A-Z0-9]{3,6})",
            r"学校(?:代号|代码)[:：]?\s*([A-Z0-9]{3,6})",
            r"^\s*([A-Z0-9]{4,6})\s+[\u4e00-\u9fff]",
        ],
        text,
    )
    subject_requirement = first_match(
        [
            r"(物理\s*[+＋]\s*化学)",
            r"(物理\s*[+＋]\s*不限)",
            r"(历史\s*[+＋]\s*不限)",
            r"选科要求[:：]?\s*([^，。；;]{2,20})",
            r"再选科目[:：]?\s*([^，。；;]{1,20})",
        ],
        text,
    )
    admission_type = first_match(
        [
            r"(普通(?:类|招生)?)",
            r"(中外合作(?:办学)?)",
            r"(国家专项)",
            r"(地方专项)",
            r"(高校专项)",
            r"(联合培养)",
        ],
        text,
    )
    major_name = first_match(
        [
            r"(?:专业名称|专业)[:：]?\s*([\u4e00-\u9fffA-Za-z0-9（）()·\-]{2,40})",
            r"\b\d{2,3}\s+([\u4e00-\u9fffA-Za-z0-9（）()·\-]{2,30})\s+\d+\s*人",
        ],
        text,
    )
    plan_count = first_match([r"(?:计划|招生人数)[:：]?\s*(\d+)\s*人?", r"\b(\d+)\s*人\b"], text)
    tuition = first_match([r"(?:学费|收费)[:：]?\s*(\d{3,6})\s*元?", r"\b(\d{4,6})\s*元/年\b"], text)
    campus = first_match(
        [
            r"(?:办学地点|校区|就读地点)[:：]?\s*([^，。；;]{2,30})",
            r"(威海校区|深圳校区|珠海校区|青岛校区|秦皇岛分校|马来西亚分校)",
        ],
        text,
    )
    review = confidence != "embedded-text" or not (school_name or school_code or group_code or major_name)
    return AdmissionRow(
        page=page,
        target=target,
        confidence=confidence,
        school_name=school_name,
        school_code=school_code,
        group_code=group_code,
        subject_requirement=subject_requirement,
        admission_type=admission_type,
        major_name=major_name,
        plan_count=plan_count,
        tuition=tuition,
        campus=campus,
        raw_text=text,
        needs_review=str(review).lower(),
    )


def write_csv(items: list[Snippet] | list[AdmissionRow], path: Path, fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(asdict(item))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract target-school snippets from official admission-plan PDFs."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--target", action="append", required=True, help="School, code, or group to locate.")
    parser.add_argument("--pages", help="Pages to inspect, e.g. 12,18-25.")
    parser.add_argument("--ocr", action="store_true", help="Use OCR when embedded text is missing.")
    parser.add_argument("--lang", default=os.environ.get("GAOKAO_OCR_LANG", "chi_sim+eng"))
    parser.add_argument("--context-chars", type=int, default=500)
    parser.add_argument("--line-context", type=int, default=2, help="Neighboring lines to include in --mode rows.")
    parser.add_argument("--mode", choices=["snippets", "rows"], default="snippets")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    pages_filter = parse_pages(args.pages)
    pages = (
        extract_with_pymupdf(args.pdf, pages_filter)
        or extract_with_pdfplumber(args.pdf, pages_filter)
        or extract_with_pdftotext(args.pdf, pages_filter)
    )
    confidence = "embedded-text"

    has_text = any(text.strip() for _, text in pages)
    if not has_text and args.ocr:
        pages = extract_with_ocr(args.pdf, pages_filter, args.lang)
        confidence = "ocr-review-required"
    elif not has_text:
        raise SystemExit("No embedded text found. Re-run with --ocr if this is a scanned PDF.")

    items: list[Snippet] | list[AdmissionRow]
    fieldnames: list[str]
    if args.mode == "rows":
        items = find_review_rows(pages, args.target, args.line_context, confidence)
        fieldnames = ROW_FIELDS
    else:
        items = find_snippets(pages, args.target, args.context_chars, confidence)
        fieldnames = ["page", "target", "confidence", "text"]

    if args.format == "csv":
        if not args.output:
            raise SystemExit("--output is required for CSV output.")
        write_csv(items, args.output, fieldnames)
    else:
        payload = [asdict(item) for item in items]
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(text + "\n", encoding="utf-8")
        else:
            print(text)

    if not items:
        print("No target snippets found. Check target names/codes or page range.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
