---
name: daily-tech-radar
description: Produce a daily Traditional Chinese technology radar review package from recent AI engineering, agentic coding, developer tooling, automation, and FinTech AI sources. Use when asked to track tech news, select a daily technical topic, draft a blog article, generate social distribution copy, create a weekly tech digest, or prepare a human-reviewable Markdown publishing package.
---

# Daily Tech Radar

Use this skill to run a guarded content workflow, not a free-form news summarizer. Always prefer primary sources, keep facts separate from interpretation, and stop at a human review package unless the user explicitly approves publishing.

## Operating Mode

1. Collect recent source items from configured feeds, official pages, repos, papers, and user-provided URLs.
2. Normalize and deduplicate sources before asking an LLM to reason about them.
3. Generate 3-5 candidate topics, then score them with the configured rubric.
4. Research the selected topic with primary and supporting sources.
5. Draft a Traditional Chinese article using the configured structure and brand voice.
6. Build a claim-source fact check table and revise overclaims before final packaging.
7. Generate website, LinkedIn, Threads, Facebook group, newsletter, and SEO variants.
8. Write a Markdown review package under `output/review_packages/`.
9. Ask for human review and approval. Never auto-publish without explicit approval.

## Required Resources

- Read `config/sources.yaml` before collecting sources.
- Read `config/scoring.yaml` before selecting topics.
- Read `config/brand_voice.yaml` before drafting or editing.
- Use `prompts/` for LLM steps rather than inventing new prompt chains.
- Use `schemas/` for structured outputs whenever possible.
- Use scripts for deterministic tasks:
  - `scripts/Run-DailyRadar.ps1` orchestrates the daily source run (Windows).
  - `scripts/run_daily_radar.sh` same pipeline on macOS/Linux (bash + Python 3).
  - `scripts/html_extract.py` extracts article/main body text from fetched HTML.
  - `scripts/manage_sources.py` lists/enables/disables/adds RSS feeds in `config/rss_sources.yaml`.
  - `scripts/sources_console.py` local web UI (http://127.0.0.1:8765) for the same RSS settings.
  - `scripts/watch_pages.py` checks `config/page_watch.yaml` URLs for content changes (no RSS).
  - `scripts/manage_page_watch.py` lists/adds pages and runs a manual watch scan.
  - `scripts/fetch_rss.py` fetches RSS/Atom feeds with the Python standard library.
  - `scripts/fetch_rss_from_config.py` fetches enabled RSS feeds with per-source categories from `config/rss_sources.yaml`.
  - `scripts/fetch_arxiv.py` fetches papers through the official arXiv Atom API.
  - `scripts/fetch_github_repos.py` fetches repositories through the official GitHub REST Search API.
  - `scripts/merge_sources.py` combines source outputs.
  - `scripts/normalize_sources.py` converts raw source JSON into stable source records.
  - `scripts/enrich_primary_sources.py` fetches full HTML text for the selected topic's primary URLs (use with `-InsecureSkipTlsVerify` on macOS or strict corporate TLS).
  - `scripts/http_fetch.py` shared HTTP helper (retries, timeouts) used by enrichment.
  - `scripts/build_source_brief.py` creates a human-readable daily source brief.
  - `scripts/generate_candidates_from_sources.py` creates a deterministic first-pass candidate list.
  - `scripts/score_topics.py` calculates weighted candidate scores.
  - `scripts/build_topic_selection_brief.py` creates a human-readable topic selection brief.
  - `scripts/build_draft_package.py` creates a Traditional Chinese research/outline/draft scaffold.
  - `scripts/prepare_agent_refinement.py` writes an IDE-agent refinement task without requiring API keys.
  - `scripts/Apply-AgentRefinement.ps1` explains how to hand the generated task to the IDE agent.
  - `scripts/Run-LatestRefinement.ps1` locates the newest IDE-agent refinement task.
  - `scripts/check_review_quality.py` and `scripts/Check-ReviewQuality.ps1` validate refined package quality gates.
  - `scripts/update_topic_memory.py` records recent selected topics.
  - `scripts/build_source_health_report.py` summarizes recent source step health.
  - `scripts/Cleanup-Outputs.ps1` removes old generated data/output files.
  - `scripts/build_review_package.py` assembles the final Markdown package.
  - `scripts/validate_package.py` checks that a review package has the required sections.
  - On Windows systems without Python, use the matching `.ps1` scripts.

## Quality Gates

- Do not select hype, rumors, funding-only news, or unsupported speculation.
- Every concrete claim in the article must have a source or be labeled as interpretation.
- Prefer official docs, official blogs, release notes, papers, and repository pages.
- Mark discussion forums and social posts as supporting sources, not primary evidence.
- Include `我的判斷`, `限制與風險`, and at least one practical application scenario in every article.
- For enterprise, financial, legal, compliance, or customer-data scenarios, include governance and data-risk caveats.
- Do not use confidential workplace information, customer data, or non-public company details.

## Default Output

Return or write a Markdown review package with:

- selected topic and selection reason
- source list with trust levels
- article draft
- fact-check table
- items requiring user confirmation
- LinkedIn post
- Threads post
- Facebook group post
- newsletter summary
- SEO metadata
- publishing checklist

## Escalation Points

Pause for user confirmation before:

- publishing to a CMS or social platform
- using paid APIs or authenticated connectors
- adding workplace-specific examples
- making claims about legal, regulatory, financial, or investment outcomes
