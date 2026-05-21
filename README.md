# Daily Tech Radar

以可重複的本地流程，從 RSS、GitHub REST（可選 arXiv）等來源蒐集近期技術動態，產出**繁體中文**、供人工審閱的技術雷達稿包（Markdown review package）。重點涵蓋 AI 工程、Agentic coding、開發者工具、自動化與 FinTech AI 等主題；**不會**在未經明確核准前自動發佈到 CMS 或社群平台。

## 特色

- **受控工作流**：先正規化與去重來源，再選題、研究、起草、事實查核，最後組裝審閱包，而非自由式新聞摘要。
- **單一每日指令**：`Run-DailyRadar.ps1` 串接擷取、合併、評分、草稿與（可選）IDE Agent 精修任務。
- **無 API Key 的 Agent 精修**：可產生完整 IDE 任務檔，由 Cursor / Codex 等代理執行並寫入指定輸出路徑。
- **品質閘道**：內建 review package 驗證、誇大用語檢查與 `topic_memory` 降低重複選題。
- **可設定來源與評分**：`config/sources.yaml`、`rss_sources.yaml`、`scoring.yaml`、`brand_voice.yaml` 等。

## 需求

| 項目 | 說明 |
|------|------|
| [PowerShell](https://learn.microsoft.com/powershell/) | 執行 `skills/daily-tech-radar/scripts/*.ps1` 編排腳本 |
| [Python 3](https://www.python.org/) | 擷取與轉換腳本（以標準函式庫為主，無額外 `requirements.txt`） |
| 網路 | 存取已啟用的 RSS、GitHub API；企業環境若遇 TLS 問題可使用 `-InsecureSkipTlsVerify` |

在 macOS / Linux 上請從專案根目錄執行下列 PowerShell 指令（需已安裝 `pwsh`）。

## 快速開始

### 每日執行（建議）

```powershell
.\skills\daily-tech-radar\scripts\Run-DailyRadar.ps1 -InsecureSkipTlsVerify -PrepareAgentRefinement
```

流程概要：擷取來源 → 正規化 → 候選主題與加權評分 → 繁中草稿骨架 →（可選）產生 IDE Agent 精修任務。

需要論文來源時再啟用 arXiv（預設關閉，部分代理 IP 易被限流）：

```powershell
.\skills\daily-tech-radar\scripts\Run-DailyRadar.ps1 -InsecureSkipTlsVerify -IncludeArxiv -PrepareAgentRefinement
```

### Agent 精修

```powershell
.\skills\daily-tech-radar\scripts\Run-LatestRefinement.ps1
```

依任務 metadata 的 `output_path`，請 IDE Agent 執行該任務並寫入精修後的 review package。

### 品質檢查

```powershell
.\skills\daily-tech-radar\scripts\Check-ReviewQuality.ps1 -Package <refined-package.md>
```

### 清理舊產物

```powershell
.\skills\daily-tech-radar\scripts\Cleanup-Outputs.ps1 -KeepDays 14 -DryRun
.\skills\daily-tech-radar\scripts\Cleanup-Outputs.ps1 -KeepDays 14
```

更完整的參數與路徑說明見 [USAGE.md](./USAGE.md)。

## 專案結構

```text
Daily Tech Radar/
├── README.md
├── USAGE.md
├── skills/daily-tech-radar/     # Cursor / Codex skill 本體
│   ├── SKILL.md                 # Agent 操作說明與品質規則
│   ├── config/                  # 來源、RSS、評分、品牌語氣
│   ├── prompts/                 # 固定 LLM 步驟提示詞
│   ├── schemas/                 # JSON 結構定義
│   ├── scripts/                 # Python + PowerShell 工具
│   ├── examples/                # 範例 JSON（納入版控）
│   ├── data/                    # 執行期原始/正規化資料（gitignore）
│   ├── output/                  # 簡報、候選、草稿、精修、審閱包（gitignore）
│   └── memory/                  # topic_memory.json 等（gitignore）
└── daily_tech_radar_agent_skill_spec.md
```

## 每日產物（本地、不進 Git）

執行後可優先檢視：

1. `output/source_briefs/YYYY-MM-DD-source-brief.md`
2. `output/candidates/YYYY-MM-DD-topic-selection-brief.md`
3. `output/drafts/YYYY-MM-DD/`
4. `output/review_packages/` 或 Agent 精修後的 Markdown
5. `output/source_health/YYYY-MM-DD-source-health.md`

`memory/topic_memory.json` 記錄近期入選主題，下次執行會對相似候選降權，減少連日重複同一類 Agent / runtime 故事。

## 在 Cursor 中使用

於對話中啟用或引用 `skills/daily-tech-radar` skill（見 `SKILL.md`）。Agent 應依 `prompts/` 與 `schemas/` 操作，並在發佈、付費 API、工作場域機密或法規/投資宣稱等情境前**暫停並請使用者確認**。

## 設計原則（摘要）

- 事實與詮釋分離；具體主張需有來源或標示為詮釋。
- 優先官方文件、部落格、release notes、論文與 repo；論壇與社群貼文僅作輔助。
- 文章需含「我的判斷」「限制與風險」與至少一個實務應用情境。
- 不使用未公開的公司、客戶或機密工作資訊。

## 相關文件

- [USAGE.md](./USAGE.md) — 指令與輸出目錄速查
- [skills/daily-tech-radar/SKILL.md](./skills/daily-tech-radar/SKILL.md) — Skill 契約與腳本清單
- [skills/daily-tech-radar/references/workflow.md](./skills/daily-tech-radar/references/workflow.md) — 工作流參考
- [initial-plan.md](./initial-plan.md) — MVP 邊界與後續規劃

## 授權

若倉庫未另附 `LICENSE` 檔，使用前請依你方組織政策處理；歡迎在新增授權條款後更新本節。
