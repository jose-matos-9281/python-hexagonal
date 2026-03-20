from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import TypedDict

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_EVIDENCE_MAP = REPO_ROOT / "docs/reference/evidence-map.yaml"
SKILL_EVIDENCE_MAP = (
    REPO_ROOT / "skills/python-hexagonal-usage/reference/evidence-map.yaml"
)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*\S)\s*$", re.MULTILINE)


class EvidenceMap(TypedDict):
    page_paths: list[str]
    evidence_paths: list[str]
    claim_anchors: list[tuple[str, str]]
    page_ids: list[str]
    claim_ids: list[str]


def _value(raw: str) -> str:
    return raw.split(":", 1)[1].strip()


def _parse_evidence_map(path: Path) -> EvidenceMap:
    page_paths: list[str] = []
    evidence_paths: list[str] = []
    claim_anchors: list[tuple[str, str]] = []
    page_ids: list[str] = []
    claim_ids: list[str] = []
    current_page_path: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        indent = len(raw_line) - len(raw_line.lstrip(" "))

        if not stripped:
            continue

        if stripped.startswith("- page_id:"):
            page_ids.append(_value(stripped))
            continue

        if indent == 4 and stripped.startswith("path:"):
            current_page_path = _value(stripped)
            page_paths.append(current_page_path)
            continue

        if stripped.startswith("- claim_id:"):
            claim_ids.append(_value(stripped))
            continue

        if indent == 8 and stripped.startswith("doc_anchor:"):
            assert current_page_path is not None
            claim_anchors.append((current_page_path, _value(stripped)))
            continue

        if stripped.startswith("- path:"):
            evidence_paths.append(_value(stripped))

    return {
        "page_paths": page_paths,
        "evidence_paths": evidence_paths,
        "claim_anchors": claim_anchors,
        "page_ids": page_ids,
        "claim_ids": claim_ids,
    }


def _slugify(heading: str) -> str:
    heading = heading.replace("`", "")
    heading = re.sub(r"[^\w\s-]", "", heading.lower())
    heading = re.sub(r"\s+", "-", heading.strip())
    heading = re.sub(r"-+", "-", heading)
    return heading.strip("-")


def _anchors_for(path: Path) -> set[str]:
    content = path.read_text(encoding="utf-8")
    return {_slugify(match.group(2)) for match in HEADING_PATTERN.finditer(content)}


def test_evidence_maps_stay_in_sync() -> None:
    assert DOCS_EVIDENCE_MAP.read_text(
        encoding="utf-8"
    ) == SKILL_EVIDENCE_MAP.read_text(encoding="utf-8")


def test_evidence_map_paths_exist_and_ids_are_unique() -> None:
    parsed = _parse_evidence_map(DOCS_EVIDENCE_MAP)
    all_paths: list[str] = parsed["page_paths"] + parsed["evidence_paths"]

    missing_paths = [
        relative for relative in all_paths if not (REPO_ROOT / relative).exists()
    ]
    assert not missing_paths

    duplicate_page_ids = [
        page_id for page_id, count in Counter(parsed["page_ids"]).items() if count > 1
    ]
    duplicate_claim_ids = [
        claim_id
        for claim_id, count in Counter(parsed["claim_ids"]).items()
        if count > 1
    ]

    assert not duplicate_page_ids
    assert not duplicate_claim_ids


def test_claim_anchors_match_markdown_headings() -> None:
    parsed = _parse_evidence_map(DOCS_EVIDENCE_MAP)
    anchors_by_page: dict[str, set[str]] = {}

    missing_anchors: list[str] = []
    for relative_path, anchor in parsed["claim_anchors"]:
        page_anchors = anchors_by_page.setdefault(
            relative_path, _anchors_for(REPO_ROOT / relative_path)
        )
        if anchor not in page_anchors:
            missing_anchors.append(f"{relative_path}#{anchor}")

    assert not missing_anchors
