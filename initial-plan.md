# Daily Tech Radar Skill Initial Plan

## Current Implementation

The first implementation is a local Codex skill at:

```text
skills/daily-tech-radar/
```

It implements the MVP as a guarded review-package workflow:

1. Configure trusted sources and scoring rules.
2. Normalize collected source items.
3. Generate and score topic candidates.
4. Research, outline, draft, fact-check, edit, and distribute through fixed prompts.
5. Assemble a Markdown review package.
6. Require human approval before any publishing step.

The daily source run now has a single command:

```powershell
.\skills\daily-tech-radar\scripts\Run-DailyRadar.ps1 -InsecureSkipTlsVerify
```

It fetches RSS and GitHub REST sources by default, optionally fetches arXiv with `-IncludeArxiv`, merges sources, normalizes them, and writes a daily source brief for the later IDE-agent topic-selection step.
It also generates first-pass topic candidates, weighted scores, and a topic selection brief.

## MVP Boundary

This version intentionally does not publish to CMS, LinkedIn, Threads, Facebook, or newsletter services. It only creates local Markdown review packages.

## Next Implementation Steps

1. Review the generated topic selection brief and decide whether deterministic candidates are good enough.
2. Add an LLM refinement step that can merge duplicate candidates, improve angles, or reject weak topics.
3. Add optional CMS draft integration after 5-10 successful manual runs.
4. Add performance tracking only after the article format is stable.

arXiv is disabled by default because the corporate proxy often returns rate-limit errors. Add `-IncludeArxiv` only when you explicitly want paper sources.

## Current Daily Handoff Files

After running `Run-DailyRadar.ps1`, review these files in order:

1. `output/source_briefs/YYYY-MM-DD-source-brief.md`
2. `output/candidates/YYYY-MM-DD-topic-selection-brief.md`
3. `output/candidates/YYYY-MM-DD-candidates.json`
4. `output/candidates/YYYY-MM-DD-scores.json`

The topic selection brief is now the main handoff into the LLM research and drafting steps.

The first Traditional Chinese scaffold is generated under:

```text
output/drafts/YYYY-MM-DD/
output/review_packages/YYYY-MM-DD-*.md
```

Professional terms such as Agent, runtime, orchestration, access control, LLM, MCP, API, and DevTools may remain in English.

## LLM Refinement

Run with IDE-agent refinement handoff enabled:

```powershell
.\skills\daily-tech-radar\scripts\Run-DailyRadar.ps1 -InsecureSkipTlsVerify -PrepareAgentRefinement
```

No API key is required. The script writes a complete IDE-agent task under `output/refinements/YYYY-MM-DD/`; ask the IDE agent to execute that task and write the refined Markdown package to the specified output path.

Convenience tools:

```powershell
.\skills\daily-tech-radar\scripts\Run-LatestRefinement.ps1
.\skills\daily-tech-radar\scripts\Check-ReviewQuality.ps1 -Package <refined-package.md>
.\skills\daily-tech-radar\scripts\Cleanup-Outputs.ps1 -KeepDays 14 -DryRun
```

RSS metadata is now loaded from `config/rss_sources.yaml`, including per-source categories.

Daily runs update `memory/topic_memory.json` and `output/source_health/YYYY-MM-DD-source-health.md`.

## Python Runtime Note

The corporate Windows policy blocked the official MSI installer, so this project uses the official Python embeddable runtime installed under the user profile. The scripts avoid third-party packages and use only the standard library.

Use `skills/daily-tech-radar/scripts/Run-Python.ps1` when a fresh PowerShell session has not picked up the user PATH yet.
