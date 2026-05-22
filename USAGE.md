# Daily Tech Radar Usage

## Daily Run

Run the daily local workflow.

**Windows (PowerShell):**

```powershell
.\skills\daily-tech-radar\scripts\Run-DailyRadar.ps1 -InsecureSkipTlsVerify -PrepareAgentRefinement
```

**macOS / Linux (bash):**

```bash
./skills/daily-tech-radar/scripts/run_daily_radar.sh
```

Defaults: `INSECURE_SKIP_TLS_VERIFY=1`, `PREPARE_AGENT_REFINEMENT=1`. Disable TLS skip: `INSECURE_SKIP_TLS_VERIFY=0 ./skills/daily-tech-radar/scripts/run_daily_radar.sh`

This fetches enabled RSS sources and GitHub REST results, skips arXiv by default, normalizes sources, selects candidate topics, **downloads full HTML for the selected topic's primary URLs** (`enrich_primary_sources.py`), builds a Traditional Chinese draft package, and prepares an IDE-agent refinement task.

On macOS or locked-down TLS environments, keep **`-InsecureSkipTlsVerify`** so RSS and primary-page fetches succeed (otherwise refinement may fall back to RSS summaries only).

Use arXiv only when needed:

```powershell
.\skills\daily-tech-radar\scripts\Run-DailyRadar.ps1 -InsecureSkipTlsVerify -IncludeArxiv -PrepareAgentRefinement
```

## Refinement

Find the latest IDE-agent refinement task:

```powershell
.\skills\daily-tech-radar\scripts\Run-LatestRefinement.ps1
```

Then ask the IDE agent to execute that task and write the refined review package to the metadata `output_path`.

## Quality Check

Check a refined package:

```powershell
.\skills\daily-tech-radar\scripts\Check-ReviewQuality.ps1 -Package <refined-package.md>
```

The checker verifies core sections, the fact-check table, manual-confirmation notes, and banned hype terms.

## Cleanup

Preview cleanup:

```powershell
.\skills\daily-tech-radar\scripts\Cleanup-Outputs.ps1 -KeepDays 14 -DryRun
```

Actually remove generated files older than 14 days:

```powershell
.\skills\daily-tech-radar\scripts\Cleanup-Outputs.ps1 -KeepDays 14
```

Generated `data/`, `output/`, and `memory/` files are ignored by git.

## Useful Outputs

- `skills/daily-tech-radar/output/source_briefs/`
- `skills/daily-tech-radar/output/candidates/`
- `skills/daily-tech-radar/output/drafts/`
- `skills/daily-tech-radar/output/refinements/`
- `skills/daily-tech-radar/output/source_health/`
- `skills/daily-tech-radar/memory/topic_memory.json`

`topic_memory.json` records recent selected topics and is used by the next run to penalize similar candidates, so repeated Agent/runtime stories are less likely to win every day.
