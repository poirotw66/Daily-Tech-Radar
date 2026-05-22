#!/usr/bin/env python3
"""CLI for page watch configuration and manual scans."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from page_watch_io import find_page, load_page_watch, save_page_watch


def default_config() -> Path:
    return Path(__file__).resolve().parent.parent / "config" / "page_watch.yaml"


def cmd_list(args: argparse.Namespace) -> int:
    for page in load_page_watch(args.config):
        flag = "on " if page.get("enabled", True) else "off"
        print(f"[{flag}] {page.get('name')} — {page.get('url')} (every {page.get('check_interval_hours', 24)}h)")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    pages = load_page_watch(args.config)
    if find_page(pages, args.name):
        print(f"Already exists: {args.name}", file=sys.stderr)
        return 1
    cats = [c.strip() for c in args.categories.split(",") if c.strip()]
    pages.append(
        {
            "name": args.name,
            "url": args.url,
            "enabled": True,
            "priority": args.priority,
            "categories": cats,
            "check_interval_hours": args.interval_hours,
        }
    )
    save_page_watch(args.config, pages)
    print(f"Added page watch: {args.name}")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    script = Path(__file__).resolve().parent / "watch_pages.py"
    cmd = [sys.executable, str(script), "--config", str(args.config)]
    if args.insecure_skip_tls_verify:
        cmd.append("--insecure-skip-tls-verify")
    if args.brief:
        cmd.extend(["--output-brief", str(args.brief)])
    if args.items:
        cmd.extend(["--output-items", str(args.items)])
    if args.emit_baseline:
        cmd.append("--emit-baseline")
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage web page change watches")
    parser.add_argument("--config", type=Path, default=default_config())
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list").set_defaults(func=cmd_list)

    add_p = sub.add_parser("add")
    add_p.add_argument("--name", required=True)
    add_p.add_argument("--url", required=True)
    add_p.add_argument("--categories", default="AI Engineering")
    add_p.add_argument("--priority", default="medium")
    add_p.add_argument("--interval-hours", type=int, default=24)
    add_p.set_defaults(func=cmd_add)

    scan_p = sub.add_parser("scan", help="Run watch_pages.py now")
    scan_p.add_argument("--brief", type=Path)
    scan_p.add_argument("--items", type=Path)
    scan_p.add_argument("--insecure-skip-tls-verify", action="store_true")
    scan_p.add_argument("--emit-baseline", action="store_true")
    scan_p.set_defaults(func=cmd_scan)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
