# Daily Tech Radar Workflow Reference

## MVP Contract

The MVP produces a local Markdown review package only. It does not publish to a CMS, social platform, newsletter service, or scheduler.

## Recommended Daily Run

Use the orchestrator from the skill root:

```powershell
.\scripts\Run-DailyRadar.ps1 -InsecureSkipTlsVerify
```

arXiv is disabled by default because some corporate proxy egress IPs hit arXiv rate limits. Enable it only when needed:

```powershell
.\scripts\Run-DailyRadar.ps1 -InsecureSkipTlsVerify -IncludeArxiv
```

To also create an IDE-agent refinement handoff:

```powershell
.\scripts\Run-DailyRadar.ps1 -InsecureSkipTlsVerify -PrepareAgentRefinement
```

No API key is required. The refinement step writes a task under `output/refinements/YYYY-MM-DD/` for the current IDE agent/Codex session to execute.

To find the latest refinement task:

```powershell
.\scripts\Run-LatestRefinement.ps1
```

To check a refined review package:

```powershell
.\scripts\Check-ReviewQuality.ps1 -Package <path-to-refined-review-package.md>
```

RSS feeds are loaded from `config/rss_sources.yaml`. Each enabled source carries its own `categories` into source item `tags`, so OpenAI, Cloudflare, GitHub, and InfoQ items can be scored with more accurate metadata.

The daily run also updates:

- `memory/topic_memory.json` for recent selected topics.
- `output/source_health/YYYY-MM-DD-source-health.md` for source-step reliability.

Cleanup old generated files:

```powershell
.\scripts\Cleanup-Outputs.ps1 -KeepDays 14 -DryRun
.\scripts\Cleanup-Outputs.ps1 -KeepDays 14
```

`-InsecureSkipTlsVerify` is only for locked-down corporate proxy environments where Python cannot validate the local TLS interception certificate. Prefer installing the corporate root CA when possible.

The orchestrator writes:

- `data/sources/YYYY-MM-DD-rss.json`
- `data/sources/YYYY-MM-DD-arxiv.json`
- `data/sources/YYYY-MM-DD-github.json`
- `data/sources/YYYY-MM-DD-raw.json`
- `data/normalized/YYYY-MM-DD-normalized.json`
- `output/source_briefs/YYYY-MM-DD-source-brief.md`
- `output/candidates/YYYY-MM-DD-candidates.json`
- `output/candidates/YYYY-MM-DD-scores.json`
- `output/candidates/YYYY-MM-DD-topic-selection-brief.md`
- `output/drafts/YYYY-MM-DD/`
- `output/review_packages/YYYY-MM-DD-*.md`
- `output/refinements/YYYY-MM-DD/` when `-PrepareAgentRefinement` is used
- `output/logs/YYYY-MM-DD-daily-run.json`

External sources are treated as recoverable dependencies. If RSS, optional arXiv, or GitHub fails, the orchestrator writes an empty fallback JSON for that source and continues so a daily brief can still be produced from the remaining sources. Check `output/logs/YYYY-MM-DD-daily-run.json` for `failed_with_empty_fallback` or `skipped_optional_source` statuses.

Manual equivalent:

1. Collect recent source items from `config/sources.yaml` and optional user URLs.
   - RSS/Atom: `./scripts/Run-Python.ps1 scripts/fetch_rss.py --url <feed-url> --output data/sources/rss.json`
   - arXiv: `./scripts/Run-Python.ps1 scripts/fetch_arxiv.py --category cs.AI --category cs.CL --output data/sources/arxiv.json`
   - GitHub: `./scripts/Run-Python.ps1 scripts/fetch_github_repos.py --output data/sources/github.json`
2. Save raw source JSON under `data/sources/YYYY-MM-DD-raw.json`.
3. Merge fetched outputs with `scripts/merge_sources.py`.
4. Run `scripts/normalize_sources.py` to produce normalized source records.
5. Run `scripts/generate_candidates_from_sources.py` for a deterministic first pass.
6. Run `scripts/score_topics.py`.
7. Ask the IDE agent to review, improve, deduplicate, or override the candidates if needed.
8. Use `scripts/build_draft_package.py` to create a Traditional Chinese scaffold.
9. Refine the scaffold with `prompts/refine_review_package.md` or the generated IDE-agent task.
10. Run `scripts/build_review_package.py`.
11. Run `scripts/validate_package.py`.
12. Ask the user for final review and publishing approval.

## Failure Handling

- If no topic reaches `minimum_score_to_write`, produce a weekly digest or evergreen topic suggestion instead of forcing a weak daily article.
- If the fact-check status is `fail`, do not produce publishing copy until the draft is revised.
- If a source has no reliable date or primary link, mark it as supporting context only.
- If a topic touches financial, legal, regulatory, customer-data, or workplace-sensitive context, add explicit caveats and require user confirmation.
- If corporate TLS interception breaks Python certificate verification, prefer installing the corporate root CA. Use `--insecure-skip-tls-verify` only for controlled smoke tests or trusted internal runs.

## Review Standard

A package is review-ready only when:

- the article contains `我的判斷` and `限制與風險`
- the source list includes at least one primary source
- concrete claims are linked to sources
- social copy does not add new facts
- user-confirmation items are explicit
