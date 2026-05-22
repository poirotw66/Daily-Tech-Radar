#!/usr/bin/env python3
"""Local web console to enable/disable and add RSS sources."""

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
from rss_config_io import find_source, load_rss_sources, save_rss_sources


HTML_PATH = Path(__file__).resolve().parent.parent / "references" / "sources_console.html"


class ConsoleHandler(BaseHTTPRequestHandler):
    config_path: Path = default_config_path()
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
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        data = self._read_json()
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--config", type=Path, default=default_config_path())
    parser.add_argument("--no-open-browser", action="store_true")
    parser.add_argument("--insecure-skip-tls-verify", action="store_true", default=True)
    args = parser.parse_args()

    ConsoleHandler.config_path = args.config
    ConsoleHandler.insecure_tls = args.insecure_skip_tls_verify
    server = ThreadingHTTPServer((args.host, args.port), ConsoleHandler)
    url = f"http://{args.host}:{args.port}/"
    print(f"RSS source console: {url}")
    print(f"Config: {args.config}")
    if not args.no_open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
