#!/usr/bin/env python3
"""CLI to list, enable, disable, add, and smoke-test RSS sources."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_rss
from rss_config_io import find_source, load_rss_sources, save_rss_sources


def default_config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "config" / "rss_sources.yaml"


def cmd_list(args: argparse.Namespace) -> int:
    sources = load_rss_sources(args.config)
    for source in sources:
        flag = "on " if source.get("enabled", True) else "off"
        cats = ", ".join(source.get("categories") or [])
        print(f"[{flag}] {source.get('name')} — {source.get('url')}")
        if cats:
            print(f"       categories: {cats}")
        if not source.get("enabled") and source.get("disabled_reason"):
            print(f"       reason: {source['disabled_reason']}")
    print(f"\nTotal: {len(sources)} ({sum(1 for s in sources if s.get('enabled'))} enabled)")
    return 0


def cmd_enable(args: argparse.Namespace) -> int:
    sources = load_rss_sources(args.config)
    source = find_source(sources, args.name)
    if not source:
        print(f"Unknown source: {args.name}", file=sys.stderr)
        return 1
    source["enabled"] = True
    source.pop("disabled_reason", None)
    save_rss_sources(args.config, sources)
    print(f"Enabled: {source['name']}")
    return 0


def cmd_disable(args: argparse.Namespace) -> int:
    sources = load_rss_sources(args.config)
    source = find_source(sources, args.name)
    if not source:
        print(f"Unknown source: {args.name}", file=sys.stderr)
        return 1
    source["enabled"] = False
    if args.reason:
        source["disabled_reason"] = args.reason
    save_rss_sources(args.config, sources)
    print(f"Disabled: {source['name']}")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    from discover_rss import discover

    report = discover(
        args.url,
        timeout=args.timeout,
        insecure=args.insecure_skip_tls_verify,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report.get("recommended_feed"):
        print(f"\nRecommended feed: {report['recommended_feed']}")
    else:
        print("\nNo public RSS/Atom feed found.", file=sys.stderr)
    return 0 if report.get("recommended_feed") else 1


def cmd_add(args: argparse.Namespace) -> int:
    sources = load_rss_sources(args.config)
    if find_source(sources, args.name):
        print(f"Source already exists: {args.name}", file=sys.stderr)
        return 1
    categories = [part.strip() for part in args.categories.split(",") if part.strip()]
    sources.append(
        {
            "name": args.name,
            "url": args.url,
            "enabled": not args.disabled,
            "priority": args.priority,
            "categories": categories,
            **({"disabled_reason": args.reason} if args.reason else {}),
        }
    )
    save_rss_sources(args.config, sources)
    print(f"Added: {args.name}")
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    sources = load_rss_sources(args.config)
    if args.name:
        targets = [find_source(sources, args.name)]
        if targets[0] is None:
            print(f"Unknown source: {args.name}", file=sys.stderr)
            return 1
    else:
        targets = [s for s in sources if s.get("enabled", True)]

    tls = args.insecure_skip_tls_verify
    results = []
    for source in targets:
        if source is None:
            continue
        url = source.get("url", "")
        try:
            root = fetch_rss.fetch_xml(url, args.timeout, tls)
            items = fetch_rss.parse_feed(root, url, 2, source.get("categories", []))
            results.append({"name": source["name"], "status": "ok", "sample_items": len(items)})
            print(f"OK  {source['name']} ({len(items)} sample items)")
        except Exception as exc:
            results.append({"name": source.get("name"), "status": "failed", "error": str(exc)})
            print(f"FAIL {source.get('name')}: {exc}")

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(r["status"] == "ok" for r in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Daily Tech Radar RSS sources")
    parser.add_argument("--config", type=Path, default=default_config_path())
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List all RSS sources")
    list_p.set_defaults(func=cmd_list)

    enable_p = sub.add_parser("enable", help="Enable a source by name")
    enable_p.add_argument("name")
    enable_p.set_defaults(func=cmd_enable)

    disable_p = sub.add_parser("disable", help="Disable a source by name")
    disable_p.add_argument("name")
    disable_p.add_argument("--reason", default="")
    disable_p.set_defaults(func=cmd_disable)

    discover_p = sub.add_parser("discover", help="Discover RSS feed URL from a site homepage")
    discover_p.add_argument("url")
    discover_p.add_argument("--timeout", type=int, default=25)
    discover_p.add_argument("--insecure-skip-tls-verify", action="store_true")
    discover_p.set_defaults(func=cmd_discover)

    add_p = sub.add_parser("add", help="Add a new RSS source")
    add_p.add_argument("--name", required=True)
    add_p.add_argument("--url", required=True)
    add_p.add_argument("--categories", default="AI Engineering, DevTools")
    add_p.add_argument("--priority", default="medium", choices=["high", "medium", "low"])
    add_p.add_argument("--disabled", action="store_true")
    add_p.add_argument("--reason", default="")
    add_p.set_defaults(func=cmd_add)

    test_p = sub.add_parser("test", help="Smoke-test feed URLs")
    test_p.add_argument("name", nargs="?", default="")
    test_p.add_argument("--timeout", type=int, default=30)
    test_p.add_argument("--insecure-skip-tls-verify", action="store_true")
    test_p.add_argument("--json", action="store_true")
    test_p.set_defaults(func=cmd_test)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
