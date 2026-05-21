#!/usr/bin/env python3
"""Generate heuristic topic candidates from normalized source records.

This is a deterministic bridge into the later LLM topic-selection step. It
does not replace editorial judgment; it creates a first-pass candidate JSON
that can be scored, reviewed, and improved by an LLM or the user.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date, datetime
from pathlib import Path


KEYWORDS = {
    "agent": ["agent", "agents", "agentic", "claude", "autogpt", "mcp"],
    "ai_coding": ["copilot", "coding", "developer", "devtools", "claude code", "codex"],
    "automation": ["workflow", "automation", "orchestration", "support", "operations"],
    "security": ["security", "unauthorized", "access", "incident", "vulnerability"],
    "research": ["paper", "model", "research", "conjecture", "reasoning"],
    "enterprise": ["enterprise", "governance", "scale", "platform", "data warehouse"],
}


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+-]*", re.IGNORECASE)


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return " ".join(text.split())


def detect_keywords(item: dict) -> set[str]:
    text = " ".join(
        [
            item.get("title", ""),
            item.get("raw_summary", ""),
            " ".join(item.get("tags", [])),
            item.get("publisher", ""),
        ]
    ).lower()
    found = set()
    for group, words in KEYWORDS.items():
        if any(word in text for word in words):
            found.add(group)
    return found


def recency_score(published_at: str | None) -> int:
    if not published_at:
        return 3
    try:
        published = datetime.fromisoformat(published_at[:10]).date()
        days = (date.today() - published).days
    except ValueError:
        return 3
    if days <= 2:
        return 5
    if days <= 7:
        return 4
    if days <= 30:
        return 3
    return 2


def source_quality(item: dict) -> int:
    trust = item.get("trust_level")
    source_type = item.get("source_type")
    if trust == "high" and source_type in {"official_blog", "docs", "github"}:
        return 5
    if trust == "high":
        return 4
    if trust == "medium":
        return 3
    return 2


def title_tokens(title: str) -> set[str]:
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "into",
        "your",
        "you",
        "new",
        "how",
        "what",
        "why",
        "announcing",
        "release",
        "update",
    }
    return {token.lower() for token in TOKEN_RE.findall(title) if token.lower() not in stopwords and len(token) > 2}


def load_topic_memory(path: Path | None) -> list[dict]:
    if not path or not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return []
    topics = data.get("topics", data if isinstance(data, list) else [])
    return topics if isinstance(topics, list) else []


def memory_penalty(title: str, topics: list[dict]) -> dict:
    current = title_tokens(title)
    if not current:
        return {"score_penalty": 0, "similarity": 0.0, "matched_title": None}

    best_similarity = 0.0
    best_title = None
    for topic in topics:
        past_title = str(topic.get("title", ""))
        past = title_tokens(past_title)
        if not past:
            continue
        similarity = len(current & past) / len(current | past)
        if similarity > best_similarity:
            best_similarity = similarity
            best_title = past_title

    if best_similarity >= 0.55:
        penalty = 12
    elif best_similarity >= 0.35:
        penalty = 7
    elif best_similarity >= 0.22:
        penalty = 4
    else:
        penalty = 0

    return {"score_penalty": penalty, "similarity": round(best_similarity, 3), "matched_title": best_title}


def candidate_from_item(item: dict, idx: int, topics: list[dict] | None = None) -> dict:
    title = clean_text(item.get("title", "Untitled"))
    summary = clean_text(item.get("raw_summary", ""))
    keywords = detect_keywords(item)
    source_type = item.get("source_type", "news")
    publisher = item.get("publisher", "unknown")
    memory = memory_penalty(title, topics or [])

    if "security" in keywords and not ({"agent", "ai_coding", "automation"} & keywords):
        angle = "technical_explainer"
        target = "engineer"
        core_question = "What does this update imply for engineering risk, access control, and operational readiness?"
    elif "agent" in keywords or "automation" in keywords:
        angle = "workflow_case"
        target = "mixed"
        core_question = "How could this change agentic workflows, developer productivity, or enterprise automation?"
    elif source_type == "github":
        angle = "tool_review"
        target = "engineer"
        core_question = "Is this repository practically useful, or is it mostly hype?"
    elif "research" in keywords:
        angle = "technical_explainer"
        target = "engineer"
        core_question = "What is the technical shift, and does it matter for practical AI engineering?"
    else:
        angle = "practical_guide"
        target = "mixed"
        core_question = "Why does this update matter for builders, PMs, or automation-focused teams?"

    relevance = 5 if {"agent", "ai_coding", "automation"} & keywords else 3
    practicality = 5 if {"agent", "automation", "ai_coding", "enterprise"} & keywords else 3
    differentiation = 5 if {"agent", "enterprise"} <= keywords else 4 if {"agent", "security", "enterprise"} & keywords else 3
    business_value = 5 if {"automation", "enterprise"} <= keywords else 4 if {"automation", "enterprise", "security"} & keywords else 3

    if source_type == "github":
        source_quality_score = min(source_quality(item), 4)
        differentiation = max(3, differentiation - 1)
    else:
        source_quality_score = source_quality(item)

    if memory["score_penalty"] >= 7:
        differentiation = max(1, differentiation - 2)
    elif memory["score_penalty"] > 0:
        differentiation = max(1, differentiation - 1)

    memory_note = "No recent similar topic detected."
    if memory["score_penalty"] > 0:
        memory_note = (
            f"Penalized by {memory['score_penalty']} for similarity "
            f"{memory['similarity']} to recent topic: {memory['matched_title']}"
        )

    return {
        "candidate_id": f"candidate-{idx:02d}",
        "title": title,
        "core_question": core_question,
        "why_now": f"{publisher} published this source on {item.get('published_at') or 'an unknown date'}. {summary[:220]}",
        "target_reader": target,
        "content_angle": angle,
        "required_sources": [item.get("source_id")],
        "scores": {
            "relevance": relevance,
            "timeliness": recency_score(item.get("published_at")),
            "practicality": practicality,
            "differentiation": differentiation,
            "business_value": business_value,
            "source_quality": source_quality_score,
        },
        "memory_penalty": memory["score_penalty"],
        "memory_note": memory_note,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("normalized_sources", type=Path)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--topic-memory", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    sources = json.loads(args.normalized_sources.read_text(encoding="utf-8-sig"))
    topics = load_topic_memory(args.topic_memory)
    ranked = []
    for item in sources:
        keywords = detect_keywords(item)
        source_type_bonus = 8 if item.get("source_type") == "official_blog" else 4 if item.get("source_type") == "github" else 0
        rank = len(keywords) * 10 + recency_score(item.get("published_at")) + source_quality(item) + source_type_bonus
        penalty = memory_penalty(clean_text(item.get("title", "Untitled")), topics)["score_penalty"]
        rank -= penalty
        ranked.append((rank, item))
    ranked.sort(key=lambda pair: pair[0], reverse=True)

    candidates = [candidate_from_item(item, idx + 1, topics) for idx, (_, item) in enumerate(ranked[: args.limit])]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
