#!/usr/bin/env python3
"""Build canonical O*NET skill nodes for semantic matching.

This script reads O*NET text exports (tab-delimited) and produces
`data/onet_skills.json` as a list of nodes shaped for `anchor_to_onet()`:

[
  {
    "id": "2.A.1.a",
    "title": "Reading Comprehension",
    "importance": 0.82,
    "aliases": ["reading comprehension"],
    "category": "Skills"
  }
]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


def _normalize_importance(value: float) -> float:
    # O*NET IM scale is 1..5. Normalize to 0..1 to match contract expectations.
    clamped = max(1.0, min(5.0, value))
    return round((clamped - 1.0) / 4.0, 4)


def _generate_aliases(title: str) -> list[str]:
    aliases = set()
    base = " ".join(title.split())
    if not base:
        return []

    aliases.add(base.lower())

    if "(" in base and ")" in base:
        aliases.add(base.split("(", 1)[0].strip().lower())

    if " and " in base.lower():
        aliases.add(base.lower().replace(" and ", " & "))
    if " & " in base:
        aliases.add(base.lower().replace(" & ", " and "))

    aliases.discard(base.lower())
    aliases.discard("")
    return sorted(aliases)


def _make_stable_id(prefix: str, text: str) -> str:
    digest = hashlib.sha1(text.strip().lower().encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _read_elements(file_path: Path, category: str) -> dict[str, dict]:
    scores: dict[str, list[float]] = defaultdict(list)
    names: dict[str, str] = {}

    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            element_id = (row.get("Element ID") or "").strip()
            element_name = (row.get("Element Name") or "").strip()
            scale_id = (row.get("Scale ID") or "").strip()

            if not element_id or not element_name:
                continue

            names[element_id] = element_name

            if scale_id != "IM":
                continue

            raw_value = (row.get("Data Value") or "").strip()
            try:
                scores[element_id].append(float(raw_value))
            except ValueError:
                continue

    result: dict[str, dict] = {}
    for element_id, element_name in names.items():
        values = scores.get(element_id, [])
        importance = _normalize_importance(sum(values) / len(values)) if values else 0.5
        result[element_id] = {
            "id": element_id,
            "title": element_name,
            "importance": importance,
            "aliases": _generate_aliases(element_name),
            "category": category,
        }
    return result


def _read_work_activities(file_path: Path) -> dict[str, dict]:
    scores: dict[str, list[float]] = defaultdict(list)
    names: dict[str, str] = {}

    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            element_id = (row.get("Element ID") or "").strip()
            element_name = (row.get("Element Name") or "").strip()
            scale_id = (row.get("Scale ID") or "").strip()

            if not element_id or not element_name:
                continue

            names[element_id] = element_name
            if scale_id != "IM":
                continue

            raw_value = (row.get("Data Value") or "").strip()
            try:
                scores[element_id].append(float(raw_value))
            except ValueError:
                continue

    nodes: dict[str, dict] = {}
    for element_id, element_name in names.items():
        values = scores.get(element_id, [])
        importance = _normalize_importance(sum(values) / len(values)) if values else 0.5
        nodes[element_id] = {
            "id": element_id,
            "title": element_name,
            "importance": importance,
            "aliases": _generate_aliases(element_name),
            "category": "WorkActivities",
        }
    return nodes


def _read_technology_vocab(file_path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}

    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            title = (row.get("Example") or "").strip()
            if not title:
                continue

            node_id = _make_stable_id("TECH", title)
            item = rows.setdefault(
                node_id,
                {
                    "id": node_id,
                    "title": title,
                    "aliases": set(_generate_aliases(title)),
                    "commodity": set(),
                    "count": 0,
                    "hot": 0,
                    "demand": 0,
                },
            )
            item["count"] += 1

            commodity_title = (row.get("Commodity Title") or "").strip()
            if commodity_title and commodity_title.lower() != title.lower():
                item["aliases"].add(commodity_title.lower())
                item["commodity"].add(commodity_title.lower())

            commodity_code = (row.get("Commodity Code") or "").strip()
            if commodity_code:
                item["aliases"].add(commodity_code)

            if (row.get("Hot Technology") or "").strip().upper() == "Y":
                item["hot"] += 1
            if (row.get("In Demand") or "").strip().upper() == "Y":
                item["demand"] += 1

    if not rows:
        return {}

    max_count = max(item["count"] for item in rows.values())
    nodes: dict[str, dict] = {}
    for node_id, item in rows.items():
        freq = math.log1p(item["count"]) / math.log1p(max_count)
        hot_ratio = item["hot"] / item["count"]
        demand_ratio = item["demand"] / item["count"]

        # Frequency drives stability; demand flags boost ranking for modern tools.
        importance = round(min(1.0, 0.25 + 0.45 * freq + 0.20 * hot_ratio + 0.10 * demand_ratio), 4)

        nodes[node_id] = {
            "id": node_id,
            "title": item["title"],
            "importance": importance,
            "aliases": sorted(item["aliases"]),
            "category": "Technology",
        }
    return nodes


def _read_tools_vocab(file_path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}

    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            title = (row.get("Example") or "").strip()
            if not title:
                continue

            node_id = _make_stable_id("TOOL", title)
            item = rows.setdefault(
                node_id,
                {
                    "id": node_id,
                    "title": title,
                    "aliases": set(_generate_aliases(title)),
                    "count": 0,
                },
            )
            item["count"] += 1

            commodity_title = (row.get("Commodity Title") or "").strip()
            if commodity_title and commodity_title.lower() != title.lower():
                item["aliases"].add(commodity_title.lower())

            commodity_code = (row.get("Commodity Code") or "").strip()
            if commodity_code:
                item["aliases"].add(commodity_code)

    if not rows:
        return {}

    max_count = max(item["count"] for item in rows.values())
    nodes: dict[str, dict] = {}
    for node_id, item in rows.items():
        freq = math.log1p(item["count"]) / math.log1p(max_count)
        importance = round(min(1.0, 0.20 + 0.60 * freq), 4)
        nodes[node_id] = {
            "id": node_id,
            "title": item["title"],
            "importance": importance,
            "aliases": sorted(item["aliases"]),
            "category": "Tools",
        }
    return nodes


def build_onet_nodes(raw_dir: Path, include_extended: bool = True) -> list[dict]:
    input_files = [
        ("Skills.txt", "Skills"),
        ("Abilities.txt", "Abilities"),
        ("Knowledge.txt", "Knowledge"),
    ]

    combined: dict[str, dict] = {}
    for filename, category in input_files:
        src = raw_dir / filename
        if not src.exists():
            continue
        for element_id, node in _read_elements(src, category).items():
            # Keep first category if duplicate IDs appear across files.
            combined.setdefault(element_id, node)

    if include_extended:
        work_activities_file = raw_dir / "Work Activities.txt"
        if work_activities_file.exists():
            for node_id, node in _read_work_activities(work_activities_file).items():
                combined.setdefault(node_id, node)

        tech_file = raw_dir / "Technology Skills.txt"
        if tech_file.exists():
            for node_id, node in _read_technology_vocab(tech_file).items():
                combined.setdefault(node_id, node)

        tools_file = raw_dir / "Tools Used.txt"
        if tools_file.exists():
            for node_id, node in _read_tools_vocab(tools_file).items():
                combined.setdefault(node_id, node)

    return sorted(combined.values(), key=lambda n: n["title"].lower())


def main() -> None:
    parser = argparse.ArgumentParser(description="Build canonical O*NET skills JSON")
    parser.add_argument(
        "--raw-dir",
        default="data/db_30_1_text",
        help="Directory containing O*NET text exports",
    )
    parser.add_argument(
        "--out",
        default="data/onet_skills.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Only include Skills/Abilities/Knowledge (smaller set)",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_path = Path(args.out)

    if not raw_dir.exists():
        raise SystemExit(f"Raw O*NET directory not found: {raw_dir}")

    nodes = build_onet_nodes(raw_dir, include_extended=not args.compact)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=2)

    print(f"Wrote {len(nodes)} O*NET nodes to {out_path}")


if __name__ == "__main__":
    main()
