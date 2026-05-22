"""Tests for html_extract."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from html_extract import extract_main_html, html_to_text, trim_boilerplate


def test_extract_prefers_article_tag() -> None:
    body = "Body paragraph. " * 40
    html_doc = f"""
    <html><body><nav>Menu</nav>
    <article><h1>Title</h1><p>{body}</p></article>
    <footer>Copyright</footer></body></html>
    """
    fragment = extract_main_html(html_doc)
    assert "Body paragraph" in fragment
    assert "Menu" not in fragment


def test_trim_boilerplate_cuts_related_posts() -> None:
    text = ("Intro content here. " * 30) + "Related posts More noise"
    trimmed = trim_boilerplate(text)
    assert "Related posts" not in trimmed
    assert "More noise" not in trimmed


def test_html_to_text_respects_max_chars() -> None:
    html_doc = "<article>" + ("word " * 5000) + "</article>"
    out = html_to_text(html_doc, max_chars=100)
    assert len(out) <= 120
    assert "[truncated]" in out
