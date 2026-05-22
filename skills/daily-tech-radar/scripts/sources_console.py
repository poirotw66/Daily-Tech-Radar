#!/usr/bin/env python3
"""Local web console for RSS sources and page watch (no-RSS listing pages)."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_rss
from discover_rss import discover
from manage_sources import default_config_path
from page_watch_io import find_page, load_page_watch, save_page_watch
from rss_config_io import find_source, load_rss_sources, save_rss_sources
from watch_pages import load_state, run_watch_scan, state_summary


HTML_PATH = Path(__file__).resolve().parent.parent / "references" / "sources_console.html"


def default_page_watch_config() -> Path:
    return Path(__file__).resolve().parent.parent / "config" / "page_watch.yaml"


def default_page_watch_state() -> Path:
    return Path(__file__).resolve().parent.parent / "memory" / "page_watch_state.json"


class ConsoleHandler(BaseHTTPRequestHandler):
    config_path: Path = default_config_path()
    page_watch_path: Path = default_page_watch_config()
    page_watch_state_path: Path = default_page_watch_state()
    insecure_tls: bool = True

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def _page_watch_payload(self) -> dict:
        pages = load_page_watch(self.page_watch_path)
        state = load_state(self.page_watch_state_path)
        return {
            "pages": pages,
            "config": str(self.page_watch_path),
            "state_path": str(self.page_watch_state_path),
            "state_updated_at": state.get("updated_at", ""),
            "summaries": state_summary(pages, state),
        }

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            content = HTML_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        if path == "/api/sources":
            sources = load_rss_sources(self.config_path)
            self._send_json(200, {"sources": sources, "config": str(self.config_path)})
            return
        if path == "/api/page-watch":
            self._send_json(200, self._page_watch_payload())
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        data = self._read_json()

        if path.startswith("/api/page-watch"):
            self._post_page_watch(path, data)
            return

        sources = load_rss_sources(self.config_path)

        if path == "/api/sources/toggle":
            name = str(data.get("name", "")).strip()
            source = find_source(sources, name)
            if not source:
                self._send_json(404, {"error": f"Unknown source: {name}"})
                return
            source["enabled"] = bool(data.get("enabled", True))
            if source["enabled"]:
                source.pop("disabled_reason", None)
            save_rss_sources(self.config_path, sources)
            self._send_json(200, {"ok": True, "name": name, "enabled": source["enabled"]})
            return

        if path == "/api/sources/add":
            name = str(data.get("name", "")).strip()
            url = str(data.get("url", "")).strip()
            if not name or not url:
                self._send_json(400, {"error": "name and url are required"})
                return
            if find_source(sources, name):
                self._send_json(409, {"error": f"Source already exists: {name}"})
                return
            categories = [
                part.strip()
                for part in str(data.get("categories", "AI Engineering")).split(",")
                if part.strip()
            ]
            sources.append(
                {
                    "name": name,
                    "url": url,
                    "enabled": bool(data.get("enabled", True)),
                    "priority": str(data.get("priority", "medium")),
                    "categories": categories,
                }
            )
            save_rss_sources(self.config_path, sources)
            self._send_json(200, {"ok": True, "name": name})
            return

        if path == "/api/sources/discover":
            page_url = str(data.get("url", "")).strip()
            if not page_url:
                self._send_json(400, {"error": "url is required"})
                return
            report = discover(
                page_url,
                timeout=int(data.get("timeout", 25)),
                insecure=bool(data.get("insecure_skip_tls_verify", self.insecure_tls)),
            )
            self._send_json(200, report)
            return

        if path == "/api/sources/test":
            name = str(data.get("name", "")).strip()
            insecure = bool(data.get("insecure_skip_tls_verify", self.insecure_tls))
            timeout = int(data.get("timeout", 30))
            targets = (
                [find_source(sources, name)]
                if name
                else [s for s in sources if s.get("enabled", True)]
            )
            results = []
            for source in targets:
                if source is None:
                    continue
                url = source.get("url", "")
                try:
                    root = fetch_rss.fetch_xml(url, timeout, insecure)
                    items = fetch_rss.parse_feed(root, url, 2, source.get("categories", []))
                    entry = {"name": source["name"], "status": "ok", "sample_items": len(items)}
                except Exception as exc:
                    entry = {"name": source.get("name"), "status": "failed", "error": str(exc)}
                results.append(entry)
            if name and results:
                self._send_json(200, results[0])
            else:
                self._send_json(200, {"results": results})
            return

        self._send_json(404, {"error": "not found"})

    def _post_page_watch(self, path: str, data: dict) -> None:
        pages = load_page_watch(self.page_watch_path)

        if path == "/api/page-watch/toggle":
            name = str(data.get("name", "")).strip()
            page = find_page(pages, name)
            if not page:
                self._send_json(404, {"error": f"Unknown page: {name}"})
                return
            page["enabled"] = bool(data.get("enabled", True))
            save_page_watch(self.page_watch_path, pages)
            self._send_json(200, {"ok": True, "name": name, "enabled": page["enabled"]})
            return

        if path == "/api/page-watch/add":
            name = str(data.get("name", "")).strip()
            url = str(data.get("url", "")).strip()
            if not name or not url:
                self._send_json(400, {"error": "name and url are required"})
                return
            if find_page(pages, name):
                self._send_json(409, {"error": f"Page watch already exists: {name}"})
                return
            categories = [
                part.strip()
                for part in str(data.get("categories", "AI Engineering")).split(",")
                if part.strip()
            ]
            pages.append(
                {
                    "name": name,
                    "url": url,
                    "enabled": bool(data.get("enabled", True)),
                    "priority": str(data.get("priority", "medium")),
                    "categories": categories,
                    "check_interval_hours": int(data.get("check_interval_hours", 24)),
                }
            )
            save_page_watch(self.page_watch_path, pages)
            self._send_json(200, {"ok": True, "name": name})
            return

        if path == "/api/page-watch/scan":
            name = str(data.get("name", "")).strip()
            page_names = [name] if name else None
            only_enabled = not bool(data.get("include_disabled", False))
            if page_names and not only_enabled:
                only_enabled = False
            try:
                report = run_watch_scan(
                    config=self.page_watch_path,
                    state_path=self.page_watch_state_path,
                    insecure_skip_tls_verify=bool(
                        data.get("insecure_skip_tls_verify", self.insecure_tls)
                    ),
                    emit_baseline=bool(data.get("emit_baseline", False)),
                    only_enabled=only_enabled if not page_names else False,
                    page_names=page_names,
                    timeout=int(data.get("timeout", 60)),
                    link_limit=int(data.get("link_limit", 40)),
                )
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})
                return
            self._send_json(
                200,
                {
                    "ok": True,
                    "checked": report["checked"],
                    "changed": report["changed"],
                    "results": report["results"],
                    "items": report["items"],
                    "summaries": report["summaries"],
                },
            )
            return

        self._send_json(404, {"error": "not found"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--config", type=Path, default=default_config_path())
    parser.add_argument("--page-watch-config", type=Path, default=default_page_watch_config())
    parser.add_argument("--page-watch-state", type=Path, default=default_page_watch_state())
    parser.add_argument("--no-open-browser", action="store_true")
    parser.add_argument("--insecure-skip-tls-verify", action="store_true", default=True)
    args = parser.parse_args()

    ConsoleHandler.config_path = args.config
    ConsoleHandler.page_watch_path = args.page_watch_config
    ConsoleHandler.page_watch_state_path = args.page_watch_state
    ConsoleHandler.insecure_tls = args.insecure_skip_tls_verify
    server = ThreadingHTTPServer((args.host, args.port), ConsoleHandler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Source console: {url}")
    print(f"RSS config: {args.config}")
    print(f"Page watch: {args.page_watch_config}")
    if not args.no_open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
