"""Read and write config/page_watch.yaml."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from rss_config_io import format_inline_list, parse_inline_list


def load_page_watch(path: Path) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_pages = False

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "page_watch:":
            in_pages = True
            continue
        if stripped == "policy:":
            break
        if not in_pages:
            continue

        if re.match(r"^\s*-\s+name:\s*", line):
            if current:
                pages.append(current)
            current = {"enabled": True, "categories": [], "check_interval_hours": 24}
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
        elif key == "check_interval_hours":
            current[key] = int(value)
        else:
            current[key] = value

    if current:
        pages.append(current)
    return pages


def load_policy_tail(path: Path) -> str:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == "policy:":
            start = index
            break
    if start is None:
        return "policy:\n  note: Managed by page watch tools\n"
    return "\n".join(lines[start:]) + "\n"


def save_page_watch(path: Path, pages: list[dict[str, Any]]) -> None:
    blocks: list[str] = ["page_watch:"]
    for page in pages:
        blocks.append(f"  - name: {page['name']}")
        blocks.append(f"    url: {page.get('url', '')}")
        blocks.append(f"    enabled: {str(bool(page.get('enabled', True))).lower()}")
        if page.get("priority"):
            blocks.append(f"    priority: {page['priority']}")
        categories = page.get("categories") or []
        blocks.append(f"    categories: {format_inline_list(list(categories))}")
        hours = page.get("check_interval_hours", 24)
        blocks.append(f"    check_interval_hours: {hours}")
    body = "\n".join(blocks) + "\n\n"
    body += load_policy_tail(path) if path.exists() else "policy:\n  note: Page watch config\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def find_page(pages: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    target = name.strip().lower()
    for page in pages:
        if str(page.get("name", "")).strip().lower() == target:
            return page
    return None
