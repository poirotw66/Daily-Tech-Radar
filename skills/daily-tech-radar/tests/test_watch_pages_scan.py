"""Tests for page watch scan helpers."""

from __future__ import annotations

import json
from pathlib import Path

from watch_pages import evaluate_page, page_key, run_watch_scan, state_summary


SAMPLE_LISTING = b"""<!DOCTYPE html><html><body><main>
<a href="/blog/new-post-slug">New Post Title</a>
<a href="/blog/existing-one">Existing</a>
</main></body></html>"""


def test_state_summary_empty_state(tmp_path: Path) -> None:
    pages = [{"name": "Test Blog", "url": "https://claude.com/blog", "enabled": True}]
    summary = state_summary(pages, {"pages": {}})
    assert summary[0]["tracked_links"] == 0
    assert summary[0]["has_baseline"] is False


def test_run_watch_scan_baseline_then_new_link(tmp_path: Path) -> None:
    config = tmp_path / "page_watch.yaml"
    config.write_text(
        "page_watch:\n  - name: Test Blog\n    url: https://claude.com/blog\n    enabled: true\n"
        "    categories: []\n    check_interval_hours: 24\n\npolicy:\n  note: test\n",
        encoding="utf-8",
    )
    state_path = tmp_path / "state.json"

    html_first = SAMPLE_LISTING
    html_second = html_first.replace(b"new-post-slug", b"brand-new-article")

    calls = {"n": 0}

    def fake_fetch(url: str, timeout: int, insecure_skip_tls_verify: bool):
        calls["n"] += 1
        return (html_first if calls["n"] == 1 else html_second, None)

    import watch_pages as wp

    original = wp.fetch_bytes
    wp.fetch_bytes = fake_fetch
    try:
        report1 = run_watch_scan(config=config, state_path=state_path, only_enabled=True)
        assert report1["changed"] == 0
        assert report1["results"][0]["first_seen"] is True

        report2 = run_watch_scan(config=config, state_path=state_path, only_enabled=True)
        assert report2["changed"] == 1
        assert report2["items"][0]["url"].endswith("brand-new-article")
    finally:
        wp.fetch_bytes = original

    state = json.loads(state_path.read_text(encoding="utf-8"))
    key = page_key("Test Blog")
    assert "brand-new-article" in "".join(state["pages"][key]["article_link_urls"])


def test_evaluate_page_detects_new_url() -> None:
    page = {"name": "X", "url": "https://claude.com/blog", "categories": []}
    previous = {
        "article_link_urls": ["https://claude.com/blog/existing-one"],
        "content_hash": "abc",
    }
    row, items, _ = evaluate_page(
        page,
        SAMPLE_LISTING,
        previous,
        max_chars=5000,
        emit_baseline=False,
        run_date="2026-05-21",
        link_limit=40,
    )
    assert row["changed"] is True
    assert len(items) == 1
    assert items[0]["watch_signal"] == "new_listing_link"
