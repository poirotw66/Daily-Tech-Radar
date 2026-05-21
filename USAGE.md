# Daily Tech Radar Usage

## Daily Run

Run the daily local workflow:

```powershell
.\skills\daily-tech-radar\scripts\Run-DailyRadar.ps1 -InsecureSkipTlsVerify -PrepareAgentRefinement
```

This fetches enabled RSS sources and GitHub REST results, skips arXiv by default, normalizes sources, selects candidate topics, builds a Traditional Chinese draft package, and prepares an IDE-agent refinement task.

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
