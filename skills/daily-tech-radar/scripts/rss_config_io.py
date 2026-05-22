"""Read and write config/rss_sources.yaml for Daily Tech Radar."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    body = value[1:-1].strip()
    if not body:
        return []
    return [part.strip().strip("'\"") for part in body.split(",") if part.strip()]


def format_inline_list(items: list[str]) -> str:
    if not items:
        return "[]"
    inner = ", ".join(items)
    return f"[{inner}]"


def load_rss_sources(path: Path) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_sources = False

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "rss_sources:":
            in_sources = True
            continue
        if stripped == "policy:":
            break
        if not in_sources:
            continue

        if re.match(r"^\s*-\s+name:\s*", line):
            if current:
                sources.append(current)
            current = {"enabled": True, "categories": []}
            current["name"] = stripped.split("name:", 1)[1].strip()
            continue
        if current is None or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "enabled":
            current[key] = value.lower() != "false"
        elif key == "categories":
            current[key] = parse_inline_list(value)
        elif key == "site_url":
            current[key] = value
        else:
            current[key] = value

    if current:
        sources.append(current)
    return sources


def load_policy_tail(path: Path) -> str:
    """Return YAML text from 'policy:' through end of file (preserved on save)."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == "policy:":
            start = index
            break
    if start is None:
        return (
            "policy:\n"
            "  note: Managed by manage_sources.py / sources_console.py\n"
            "  recommended_mvp_sources: []\n"
        )
    return "\n".join(lines[start:]) + "\n"


def save_rss_sources(path: Path, sources: list[dict[str, Any]]) -> None:
    blocks: list[str] = ["rss_sources:"]
    for source in sources:
        blocks.append(f"  - name: {source['name']}")
        if source.get("site_url"):
            blocks.append(f"    site_url: {source['site_url']}")
        blocks.append(f"    url: {source.get('url', '')}")
        blocks.append(f"    enabled: {str(bool(source.get('enabled', True))).lower()}")
        if source.get("priority"):
            blocks.append(f"    priority: {source['priority']}")
        categories = source.get("categories") or []
        blocks.append(f"    categories: {format_inline_list(list(categories))}")
        if source.get("disabled_reason"):
            blocks.append(f"    disabled_reason: {source['disabled_reason']}")
    body = "\n".join(blocks) + "\n\n"
    body += load_policy_tail(path) if path.exists() else (
        "policy:\n  note: Edit RSS feeds via manage_sources.py or sources_console.py\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def find_source(sources: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    target = name.strip().lower()
    for source in sources:
        if str(source.get("name", "")).strip().lower() == target:
            return source
    return None
