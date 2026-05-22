# Daily Tech Radar Usage

## 網頁變更監控（無 RSS）

適用 **沒有 RSS** 的列表頁／官網（例如 [Claude Blog](https://claude.com/blog)）。以**文章連結列表**比對（新 URL 才觸發）；解析不到連結時才退回正文指紋。**第一次執行只建立連結基準**，之後每個新文章 URL 會各產生一筆來源訊號。

設定檔：`skills/daily-tech-radar/config/page_watch.yaml`（預設含 Claude Blog、Anthropic Newsroom）。

```bash
# 手動掃描（寫入簡報與變更項目 JSON）
python3 skills/daily-tech-radar/scripts/manage_page_watch.py list
python3 skills/daily-tech-radar/scripts/manage_page_watch.py scan \
  --insecure-skip-tls-verify \
  --brief skills/daily-tech-radar/output/page_watch/$(date +%Y-%m-%d)-page-watch-brief.md \
  --items skills/daily-tech-radar/data/sources/$(date +%Y-%m-%d)-page-watch.json

# 新增頁面
python3 skills/daily-tech-radar/scripts/manage_page_watch.py add \
  --name "Example News" --url "https://example.com/news"
```

**定期執行**：將 `run_daily_radar.sh` 或 `Run-DailyRadar.ps1` 排進 cron / launchd（例如每日 09:00）；該步驟已內建 `watch_pages.py`。狀態保存在 `skills/daily-tech-radar/memory/page_watch_state.json`（已 gitignore）。

## RSS 來源管理

RSS 清單在 `skills/daily-tech-radar/config/rss_sources.yaml`（`enabled: true` 的才會被每日流程擷取）。GitHub REST 與 arXiv 仍由 `Run-DailyRadar.ps1` / `run_daily_radar.sh` 參數控制，不在此檔。

### 瀏覽器主控台（建議）

```bash
python3 skills/daily-tech-radar/scripts/sources_console.py
```

預設開啟 http://127.0.0.1:8765/ 。分頁 **RSS 來源**（勾選啟用、探索 Feed、測試）與 **網頁監控**（Page Watch：啟停、新增列表頁、掃描連結比對、查看追蹤連結數與新 URL 結果）。

### 指令列

```bash
python3 skills/daily-tech-radar/scripts/manage_sources.py list
python3 skills/daily-tech-radar/scripts/manage_sources.py enable "Vercel Blog"
python3 skills/daily-tech-radar/scripts/manage_sources.py disable "LangChain Blog" --reason "proxy redirect"
python3 skills/daily-tech-radar/scripts/manage_sources.py add --name "Example Blog" --url "https://example.com/feed.xml" --categories "AI Engineering"
python3 skills/daily-tech-radar/scripts/manage_sources.py test --insecure-skip-tls-verify
python3 skills/daily-tech-radar/scripts/manage_sources.py discover https://claude.com/blog --insecure-skip-tls-verify
```

**Claude Blog（https://claude.com/blog）**：截至自動探索，**沒有公開 RSS/Atom**（常見路徑與 HTML `link rel=alternate` 皆無有效 feed）。`rss_sources.yaml` 已保留一筆停用的「Claude Blog」紀錄（`site_url` + 說明）。相關官方動態可手動參考 [Anthropic Newsroom](https://www.anthropic.com/news)（同樣未確認 RSS）。

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
