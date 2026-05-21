# Daily Tech Radar Agent Skill 專案規格

## 1. 專案目標

建立一個可每日執行的 Agent Skill，幫助個人技術網站穩定產出一篇技術文章，並同步產出社群分發內容。整個流程由 Agent 完成，使用者只負責最後審稿、修改觀點與批准發布。

這個系統不是單純的 AI 文章產生器，而是一個「個人技術媒體自動化工作流」。它的核心價值是：

1. 每日追蹤 AI engineering、vibe coding、developer tools、automation、FinTech AI 等技術新知。
2. 自動篩選值得寫的題目。
3. 自動整理來源、摘要、比較與技術脈絡。
4. 產生符合個人品牌語氣的文章初稿。
5. 產生網站版、LinkedIn 版、Threads 版、Facebook 社團版、Newsletter 摘要版。
6. 交付一份完整審稿包，讓使用者只需做最終把關。

---

## 2. 使用者定位

### 2.1 內容品牌定位

使用者定位為：

> 長期追蹤 AI 工程化、vibe coding、開發者工具與自動化技術，並把新技術轉化成可實作、可商業化、可企業落地的技術觀察者。

### 2.2 目標讀者

主要讀者分成四類：

1. 工程師  
   關心 AI coding、LLM app、agent、MCP、RAG、開發工具與工程實踐。

2. PM / 技術管理者  
   關心技術趨勢如何影響產品開發、MVP、團隊效率與技術決策。

3. 小企業主 / 自動化需求者  
   關心如何用 AI、表單、Google Sheet、LINE、n8n、Airtable 等工具降低重複行政工作。

4. 金融科技 / 企業應用讀者  
   關心 AI 在金融、法遵、內控、文件處理、報表與企業流程中的實際落地方式。

### 2.3 內容差異化

不要做成「技術新聞翻譯站」。每篇文章都必須包含使用者的判斷角度：

- 這件事為什麼重要？
- 它對工程流程有什麼影響？
- 它能不能被應用在自動化、小企業或企業場景？
- 它有哪些風險、限制或落地成本？
- 這件事值得現在投入，還是只是短期 hype？

---

## 3. 專案範圍

### 3.1 MVP 範圍

第一版 Agent Skill 需要完成：

1. 每日蒐集來源。
2. 篩選 3～5 個候選題目。
3. 根據評分選出 1 個主題。
4. 產生一篇網站文章草稿。
5. 產生社群分發文案。
6. 產生來源清單與事實檢查表。
7. 產出一份 Markdown 審稿包。
8. 等待使用者審稿。

MVP 不需要一開始就自動發布到網站或社群。第一階段只做到「自動產稿與審稿包」。

### 3.2 V1 範圍

V1 可以加入：

1. 網站 CMS 草稿建立。
2. 圖片產生或封面圖建議。
3. 自動生成 SEO metadata。
4. 自動保存每日資料到內容資料庫。
5. 每週自動彙整 Weekly Digest。
6. 文章表現追蹤。

### 3.3 V2 範圍

V2 可以加入：

1. 自動 A/B 測試標題。
2. 自動找出系列文題目。
3. 根據過往流量優化選題。
4. 自動建立 demo project 或 repo skeleton。
5. 把文章轉成短影片腳本。
6. 把高互動文章轉成 lead magnet 或顧問服務頁。

---

## 4. 核心使用情境

### 4.1 每日文章產出

使用者每天早上或固定時間觸發 Agent。

Agent 執行：

1. 掃描指定來源。
2. 整理今日值得注意的技術事件。
3. 依內容策略評分。
4. 選出最適合今日發布的主題。
5. 撰寫文章初稿。
6. 產出社群貼文。
7. 產出審稿包。

使用者只做：

1. 檢查事實與語氣。
2. 補上個人觀點。
3. 決定是否發布。

### 4.2 每週技術雷達

每週一次，Agent 彙整過去 7 天內容：

1. 本週最重要 5 個技術趨勢。
2. 本週工具觀察。
3. 本週值得深入研究的 repo / paper / product。
4. 下週可能延伸題目。

### 4.3 專案實作建議

當某個技術主題值得做 demo 時，Agent 額外產出：

1. Demo idea。
2. 技術架構。
3. 最小可行功能。
4. 可用工具。
5. 文章如何連到該 demo。

---

## 5. Agent Skill 高階工作流

```text
Daily Trigger
    ↓
Source Collector
    ↓
Content Deduplicator
    ↓
Topic Candidate Generator
    ↓
Topic Scorer
    ↓
Research Agent
    ↓
Outline Agent
    ↓
Draft Writer Agent
    ↓
Fact Checker Agent
    ↓
Brand Voice Editor Agent
    ↓
Distribution Agent
    ↓
Review Package Builder
    ↓
Human Final Review
    ↓
Optional Publish
```

---

## 6. Agent 模組設計

## 6.1 Source Collector Agent

### 目的

負責蒐集每日技術來源。

### 輸入

- RSS feeds
- 官方 blog URL
- GitHub trending / repo list
- Hacker News
- arXiv category
- Product Hunt / Launch notes
- 使用者手動加入的 URL

### 輸出

標準化 source item：

```json
{
  "source_id": "string",
  "title": "string",
  "url": "string",
  "source_type": "official_blog | github | paper | news | discussion | docs | launch",
  "publisher": "string",
  "published_at": "YYYY-MM-DD",
  "fetched_at": "YYYY-MM-DDTHH:mm:ssZ",
  "raw_summary": "string",
  "tags": ["AI Coding", "LLM App", "Automation"],
  "language": "en | zh | other"
}
```

### MVP 來源建議

第一版先不要太多來源，避免品質不穩。

建議來源：

1. OpenAI Blog / Docs
2. Anthropic Blog / Docs
3. GitHub Blog
4. Cloudflare Blog
5. Vercel Blog
6. Supabase Blog
7. LangChain Blog
8. Hugging Face Blog
9. Hacker News front page
10. GitHub Trending
11. arXiv cs.AI / cs.CL / cs.LG
12. InfoQ AI / Architecture

---

## 6.2 Content Deduplicator Agent

### 目的

避免同一件事情被多個來源重複計算。

### 判斷邏輯

同一事件可能出現在：

- 官方 announcement
- Hacker News 討論
- GitHub repo
- 第三方新聞
- 中文社群轉貼

Deduplicator 要把它們合併成同一 topic cluster。

### 輸出

```json
{
  "cluster_id": "string",
  "main_title": "string",
  "primary_source": "source_id",
  "supporting_sources": ["source_id_1", "source_id_2"],
  "summary": "string",
  "detected_angle": "tool_launch | model_update | framework_release | paper | security_issue | developer_workflow"
}
```

---

## 6.3 Topic Candidate Generator

### 目的

從 topic cluster 中產出 3～5 個今日候選題目。

### 候選題目格式

```json
{
  "candidate_id": "string",
  "title": "string",
  "core_question": "string",
  "why_now": "string",
  "target_reader": "engineer | pm | small_business | fintech | mixed",
  "content_angle": "technical_explainer | practical_guide | opinion | tool_review | workflow_case",
  "required_sources": ["source_id"]
}
```

### 題目產生原則

優先選擇：

1. 跟 AI engineering 有關。
2. 跟 vibe coding / agentic coding 有關。
3. 可以轉成實作或案例。
4. 對小企業自動化有啟發。
5. 對企業或金融場景有落地意義。
6. 能展現使用者的獨特判斷。

避免選擇：

1. 純八卦或融資新聞。
2. 沒有工程含量的工具宣傳。
3. 無法驗證的傳聞。
4. 只有熱度但沒有應用場景的話題。
5. 太接近公司內部敏感領域的題目。

---

## 6.4 Topic Scorer Agent

### 目的

用一致的標準選出今日主題。

### 評分維度

每個候選題目以 1～5 分評分。

| 維度 | 說明 | 權重 |
|---|---|---:|
| Relevance | 是否符合個人品牌定位 | 25% |
| Timeliness | 是否具有時效性 | 15% |
| Practicality | 是否能轉成實作或應用 | 20% |
| Differentiation | 是否能產生獨特觀點 | 20% |
| Business Value | 是否可能導向顧問、接案、服務 | 10% |
| Source Quality | 來源是否可靠 | 10% |

### 輸出

```json
{
  "selected_candidate_id": "string",
  "score_table": [
    {
      "candidate_id": "string",
      "scores": {
        "relevance": 5,
        "timeliness": 4,
        "practicality": 5,
        "differentiation": 4,
        "business_value": 3,
        "source_quality": 5
      },
      "weighted_score": 4.55,
      "reason": "string"
    }
  ],
  "selection_reason": "string"
}
```

---

## 6.5 Research Agent

### 目的

對選定題目做足夠研究，避免寫成表層整理。

### 任務

1. 閱讀 primary source。
2. 閱讀 supporting sources。
3. 找出官方說法。
4. 找出社群或工程師討論中的關鍵疑問。
5. 補充背景脈絡。
6. 列出可驗證事實。
7. 列出不能過度推論的地方。

### 輸出

```json
{
  "topic": "string",
  "source_brief": [
    {
      "source_id": "string",
      "key_points": ["string"],
      "important_quotes": ["short quote only"],
      "reliability": "high | medium | low"
    }
  ],
  "background_context": ["string"],
  "verified_facts": ["string"],
  "uncertainties": ["string"],
  "possible_angles": ["string"]
}
```

---

## 6.6 Outline Agent

### 目的

根據研究結果產生文章大綱。

### 每日文章標準結構

```md
# {標題}

## TL;DR
- 3 句話說明重點

## 發生了什麼？

## 為什麼值得注意？

## 對工程流程的影響

## 可以怎麼應用？

## 限制與風險

## 我的判斷

## 延伸閱讀
```

### 深度文章標準結構

```md
# {標題}

## TL;DR

## 背景：為什麼現在要看這件事

## 技術重點拆解

## 工程實作角度

## 商業或流程應用角度

## 企業/金融場景的可能性與限制

## 風險、坑與反方觀點

## 我的結論

## 延伸閱讀
```

---

## 6.7 Draft Writer Agent

### 目的

撰寫文章初稿。

### 寫作要求

1. 使用繁體中文。
2. 語氣專業但不要學術腔。
3. 適合工程師、PM 和商業讀者閱讀。
4. 不要過度吹捧工具。
5. 每篇必須有「我的判斷」段落。
6. 每篇必須有「限制與風險」段落。
7. 每篇必須指出至少 1 個實際應用場景。
8. 若涉及金融或企業應用，必須提醒權限、資料、合規或治理限制。

### 文章長度

| 類型 | 長度 |
|---|---:|
| Daily Note | 800～1,500 字 |
| Deep Dive | 2,000～4,000 字 |
| Weekly Digest | 1,500～2,500 字 |
| Project Build Log | 1,500～3,000 字 |

---

## 6.8 Fact Checker Agent

### 目的

降低 AI 幻覺與錯誤引用。

### 檢查項目

1. 每個具體事實是否有來源。
2. 發布日期是否正確。
3. 公司、工具、repo、paper 名稱是否正確。
4. 是否把推測寫成事實。
5. 是否有過度誇大。
6. 是否引用了低品質來源。
7. 是否涉及敏感、未公開或公司內部資訊。

### 輸出

```json
{
  "fact_check_status": "pass | needs_revision | fail",
  "issues": [
    {
      "severity": "high | medium | low",
      "text": "string",
      "problem": "string",
      "suggested_fix": "string",
      "source_needed": true
    }
  ],
  "safe_to_review": true
}
```

---

## 6.9 Brand Voice Editor Agent

### 目的

把文章調整成使用者個人風格。

### 品牌語氣

1. 清楚、務實、偏產品與工程判斷。
2. 不使用過度行銷語。
3. 少講空泛願景，多講實際影響。
4. 不自稱大師、專家、權威。
5. 常用句型：
   - 「我會把它看成……」
   - 「真正值得注意的不是……而是……」
   - 「這對小團隊的意義是……」
   - 「如果放到企業場景，第一個問題會是……」

### 避免語氣

1. 「顛覆」、「革命性」、「史詩級」等誇張形容。
2. 沒有根據的投資或商業預測。
3. 過度簡化企業落地難度。
4. 像新聞稿或工具介紹頁。

---

## 6.10 Distribution Agent

### 目的

將同一篇文章改寫為不同平台格式。

### 輸出內容

1. 個人網站完整文章。
2. LinkedIn 專業摘要。
3. Threads 連續短文。
4. Facebook 社團實用版。
5. Newsletter 摘要。
6. SEO metadata。

### LinkedIn 格式

```md
{開場洞察，1～2 句}

{事件簡述}

我覺得這件事值得注意的原因是：
1. ...
2. ...
3. ...

對工程/產品團隊來說，真正的問題不是 {A}，而是 {B}。

完整文章：{URL placeholder}
```

### Threads 格式

```md
1/ 今天看到一個值得注意的技術變化：{topic}

2/ 它表面上是 {surface}，但我覺得真正重要的是 {insight}

3/ 對小團隊來說，這代表 {practical implication}

4/ 不過要注意 {risk}

5/ 我整理了一篇完整觀察：{URL placeholder}
```

### Facebook 社團格式

```md
最近很多人在討論 {topic}。

我用比較實務的角度整理了一下，它可能適合這些情境：

- 情境 1
- 情境 2
- 情境 3

但不建議直接用在：

- 風險 1
- 風險 2

我整理了完整文章，有興趣可以看：{URL placeholder}
```

---

## 6.11 Review Package Builder

### 目的

把所有產出整理成一份使用者容易審稿的包。

### 審稿包內容

```md
# 今日技術文章審稿包

## 1. 今日主題

## 2. 為什麼選這題

## 3. 來源清單

## 4. 文章草稿

## 5. 事實檢查結果

## 6. 需要你特別確認的地方

## 7. LinkedIn 貼文

## 8. Threads 貼文

## 9. Facebook 社團貼文

## 10. Newsletter 摘要

## 11. SEO Metadata

## 12. 建議發布標籤
```

### 使用者審稿重點

Agent 必須明確標出：

1. 哪些地方是事實。
2. 哪些地方是推論。
3. 哪些地方需要使用者補個人經驗。
4. 哪些地方可能有風險。
5. 哪些地方適合改成更強的個人觀點。

---

## 7. 資料模型

## 7.1 Article Record

```json
{
  "article_id": "YYYYMMDD-topic-slug",
  "date": "YYYY-MM-DD",
  "status": "draft | review | approved | published | archived",
  "title": "string",
  "slug": "string",
  "category": "AI Coding | LLM App | Automation | FinTech AI | DevTools | Security | Data",
  "tags": ["string"],
  "summary": "string",
  "body_markdown": "string",
  "sources": ["source_id"],
  "fact_check_status": "pass | needs_revision | fail",
  "review_notes": ["string"],
  "created_at": "datetime",
  "updated_at": "datetime",
  "published_at": "datetime | null"
}
```

## 7.2 Source Record

```json
{
  "source_id": "string",
  "title": "string",
  "url": "string",
  "source_type": "string",
  "publisher": "string",
  "published_at": "date",
  "fetched_at": "datetime",
  "summary": "string",
  "trust_level": "high | medium | low",
  "used_in_articles": ["article_id"]
}
```

## 7.3 Topic Score Record

```json
{
  "candidate_id": "string",
  "date": "YYYY-MM-DD",
  "title": "string",
  "scores": {
    "relevance": 1,
    "timeliness": 1,
    "practicality": 1,
    "differentiation": 1,
    "business_value": 1,
    "source_quality": 1
  },
  "weighted_score": 0,
  "selected": false,
  "reason": "string"
}
```

---

## 8. Skill 檔案結構建議

```text
skills/
  daily-tech-radar/
    SKILL.md
    config/
      sources.yaml
      categories.yaml
      brand_voice.yaml
      scoring.yaml
      publishing.yaml
    prompts/
      collect_sources.md
      generate_candidates.md
      score_topics.md
      research_topic.md
      write_outline.md
      draft_article.md
      fact_check.md
      edit_brand_voice.md
      generate_distribution.md
      build_review_package.md
    schemas/
      source_item.schema.json
      topic_candidate.schema.json
      article.schema.json
      review_package.schema.json
    scripts/
      fetch_rss.py
      fetch_github_trending.py
      fetch_arxiv.py
      normalize_sources.py
      build_markdown_package.py
    output/
      drafts/
      review_packages/
      published/
      logs/
```

---

## 9. SKILL.md 規格草案

```md
# Daily Tech Radar Skill

## Purpose

This skill helps the user produce one daily technical article by collecting recent technical updates, selecting a high-value topic, researching reliable sources, drafting a Traditional Chinese article, generating distribution copy, and preparing a human review package.

## When to use

Use this skill when the user asks to:

- produce a daily technical article
- track AI engineering or developer tool news
- generate a technology radar post
- create a weekly tech digest
- prepare content for a personal technical website
- turn technical news into blog/social posts

## Core principles

1. Do not write generic news summaries.
2. Always include the user's practical judgment.
3. Prefer official sources and primary documentation.
4. Clearly separate verified facts from interpretation.
5. Always produce a review package before publishing.
6. Never publish automatically without explicit user approval.
7. Avoid using confidential workplace information.
8. Write in Traditional Chinese unless the user asks otherwise.

## Workflow

1. Collect sources.
2. Deduplicate and cluster related items.
3. Generate candidate topics.
4. Score topics using the configured scoring model.
5. Select one primary topic.
6. Research the topic using primary and supporting sources.
7. Draft article outline.
8. Write article draft.
9. Fact-check draft.
10. Edit for brand voice.
11. Generate distribution copy.
12. Build review package.
13. Ask user for final review.

## Output

The final output should be a Markdown review package containing:

- selected topic
- selection reason
- source list
- article draft
- fact-check notes
- LinkedIn post
- Threads post
- Facebook post
- newsletter summary
- SEO metadata
- review checklist
```

---

## 10. Prompt 規格

## 10.1 Topic Scoring Prompt

```md
You are the topic selection agent for a personal technical media site.

The user's content positioning is:
- AI engineering
- vibe coding
- developer tools
- automation workflows
- FinTech AI applications

Score each candidate topic from 1 to 5 on:
- relevance
- timeliness
- practicality
- differentiation
- business value
- source quality

Return a JSON object with weighted scores and a final selected topic.

Do not select topics that are only hype, rumors, funding news, or unsupported speculation.
```

## 10.2 Article Draft Prompt

```md
You are writing a Traditional Chinese technical article for the user's personal website.

Write with these principles:
- practical and clear
- technical but not academic
- opinionated but not exaggerated
- useful to engineers, PMs, and automation-focused readers
- include risks and limitations
- include one section called「我的判斷」

Do not merely translate or summarize the source.
Explain why this matters and how it could be used in real workflows.
```

## 10.3 Fact Check Prompt

```md
Review the article draft.

Check:
1. Which claims require sources?
2. Which statements are interpretations and should be labeled as such?
3. Are dates, product names, company names, and technical terms correct?
4. Is there any overclaiming?
5. Is there any confidential or sensitive workplace information?
6. Are there unsupported business or technology predictions?

Return:
- pass / needs_revision / fail
- issue list
- suggested fixes
```

---

## 11. 設定檔規格

## 11.1 sources.yaml

```yaml
sources:
  - name: OpenAI Blog
    type: official_blog
    url: https://openai.com/news/
    priority: high
    categories: [AI Engineering, LLM App]

  - name: Anthropic News
    type: official_blog
    url: https://www.anthropic.com/news
    priority: high
    categories: [AI Engineering, Agent]

  - name: GitHub Blog
    type: official_blog
    url: https://github.blog/
    priority: high
    categories: [DevTools]

  - name: Hacker News
    type: discussion
    url: https://news.ycombinator.com/
    priority: medium
    categories: [DevTools, AI Engineering]

  - name: arXiv cs.CL
    type: paper
    url: https://arxiv.org/list/cs.CL/recent
    priority: medium
    categories: [LLM, Research]
```

## 11.2 brand_voice.yaml

```yaml
language: zh-TW
voice:
  tone: practical, clear, technical, business-aware
  avoid:
    - hype
    - exaggerated predictions
    - generic summaries
    - empty motivational language
  required_sections:
    - TL;DR
    - 為什麼值得注意？
    - 可以怎麼應用？
    - 限制與風險
    - 我的判斷
preferred_phrases:
  - 真正值得注意的不是...而是...
  - 我會把它看成...
  - 如果放到企業場景...
  - 對小團隊來說...
```

## 11.3 scoring.yaml

```yaml
weights:
  relevance: 0.25
  timeliness: 0.15
  practicality: 0.20
  differentiation: 0.20
  business_value: 0.10
  source_quality: 0.10
minimum_score_to_write: 3.8
```

---

## 12. 審稿介面需求

MVP 可以先用 Markdown 檔審稿。

V1 可以升級成簡單 Web UI。

### 12.1 Markdown 審稿

輸出檔案：

```text
/output/review_packages/2026-05-20-topic-slug.md
```

內容包含：

- 文章草稿
- 來源
- fact check issues
- 社群貼文
- SEO
- 審稿 checklist

### 12.2 Web UI 審稿

功能：

1. 查看今日候選題目。
2. 查看為什麼選中某題。
3. 編輯文章內容。
4. 查看來源與事實檢查。
5. 編輯社群貼文。
6. 一鍵標記 approved。
7. 發布到網站 CMS。

---

## 13. 發布流程

## 13.1 MVP

Agent 只產生 Markdown。

使用者手動：

1. 打開審稿包。
2. 修改文章。
3. 貼到網站 CMS。
4. 發到社群。

## 13.2 V1

Agent 可以建立 CMS draft。

流程：

1. Agent 產生文章。
2. Agent 寫入 CMS draft。
3. 使用者在 CMS 審稿。
4. 使用者點擊發布。

## 13.3 V2

Agent 可以在使用者批准後發布。

流程：

1. Agent 產生審稿包。
2. 使用者輸入「批准發布」。
3. Agent 發布網站文章。
4. Agent 排程社群貼文。
5. Agent 記錄發布結果。

---

## 14. 品質標準

每篇文章發布前必須通過以下檢查：

### 14.1 內容品質

- 標題清楚。
- TL;DR 能在 30 秒內讓人理解重點。
- 不是單純翻譯或摘要。
- 有具體應用場景。
- 有限制與風險。
- 有使用者判斷。

### 14.2 事實品質

- 主要事實有來源。
- 日期正確。
- 工具名稱正確。
- 不把推論寫成事實。
- 不引用不可靠傳聞當主來源。

### 14.3 品牌品質

- 跟 AI engineering / automation / FinTech AI 定位一致。
- 不過度行銷。
- 不空泛。
- 能展現務實判斷。

### 14.4 風險品質

- 不包含公司內部資訊。
- 不包含客戶資料。
- 不提供未經確認的金融投資建議。
- 不誤導讀者可直接用 AI 取代高風險人工審核。

---

## 15. 成功指標

## 15.1 產出指標

| 指標 | 目標 |
|---|---:|
| 每週文章數 | 5 篇以上 |
| 每週深度文 | 1 篇 |
| 每週 Weekly Digest | 1 篇 |
| 人工審稿時間 | 每篇 15～30 分鐘內 |
| 草稿可用率 | 70% 以上 |

## 15.2 影響力指標

| 指標 | 目標 |
|---|---:|
| 網站自然流量 | 每月成長 |
| LinkedIn / Threads 收藏數 | 每週成長 |
| 訂閱電子報人數 | 每月成長 |
| 私訊詢問數 | 每月成長 |
| 合作表單提交數 | 每月成長 |

## 15.3 商業指標

| 指標 | 目標 |
|---|---:|
| 流程健檢詢問 | 每月 2～5 件 |
| 顧問 / 自動化案源 | 每季 1～3 件 |
| 文章帶來的合作對話 | 持續增加 |

---

## 16. 開發 Roadmap

## Phase 0：人工流程驗證

時間：1 週

目標：先不用寫完整系統，手動跑 5 篇文章，驗證模板與輸出品質。

交付：

1. 文章模板。
2. 審稿包模板。
3. 來源清單。
4. 選題評分表。

## Phase 1：MVP Agent Skill

時間：2～3 週

目標：完成從來源整理到審稿包產出的自動化。

交付：

1. SKILL.md。
2. prompts。
3. sources.yaml。
4. scoring.yaml。
5. review package generator。
6. 每日 Markdown 輸出。

## Phase 2：網站整合

時間：2～4 週

目標：將 approved article 建立為網站 draft。

交付：

1. CMS API integration。
2. SEO metadata。
3. article slug generator。
4. image suggestion / cover generator。

## Phase 3：社群分發與週報

時間：2～4 週

目標：自動產生跨平台內容與 Weekly Digest。

交付：

1. LinkedIn post generator。
2. Threads post generator。
3. newsletter digest。
4. weekly trend report。

## Phase 4：回饋與優化

時間：持續

目標：根據文章表現調整選題。

交付：

1. performance tracker。
2. topic memory。
3. style improvement notes。
4. high-performing article pattern analysis。

---

## 17. 風險與限制

## 17.1 最大風險：文章變成 AI 罐頭文

解法：

1. 每篇必須有「我的判斷」。
2. 每篇必須有「適用 / 不適用情境」。
3. 每週至少一篇加入實作或個人觀察。

## 17.2 事實錯誤

解法：

1. 優先官方來源。
2. 每篇附 fact check table。
3. 沒有來源的說法標成推論。

## 17.3 過度依賴短期熱點

解法：

1. 每週保留 1 篇 evergreen 技術文。
2. 建立系列文。
3. 把新聞轉成長期框架。

## 17.4 法遵與公司資訊風險

解法：

1. 不使用公司內部資訊。
2. 不使用客戶資料。
3. 金融場景只談公開、通用原則。
4. 涉及監管、投資、法律內容時加上限制與免責語氣。

---

## 18. 第一版最小可行輸出範例

每日 Agent 執行後，應產生：

```text
/output/review_packages/2026-05-20-claude-code-agentic-workflow.md
```

內容：

```md
# 今日技術文章審稿包

## 今日主題
Claude Code 的 agentic workflow 對 MVP 開發流程的影響

## 為什麼選這題
- 符合 AI coding 定位
- 跟 vibe coding 商業化路線有關
- 可延伸到小企業自動化顧問服務

## 來源清單
1. 官方來源
2. 文件來源
3. 社群討論

## 文章草稿
...

## 事實檢查
| Claim | Source | Status | Note |
|---|---|---|---|

## 需要你確認的地方
- 是否要加入個人使用經驗
- 是否要連到自動化顧問服務頁
- 是否要避免提到特定公司場景

## LinkedIn 版本
...

## Threads 版本
...

## Newsletter 摘要
...

## SEO
Title: ...
Description: ...
Slug: ...
Tags: ...
```

---

## 19. 建議優先實作順序

第一週不要急著接 CMS。

優先做：

1. sources.yaml
2. scoring.yaml
3. brand_voice.yaml
4. 文章模板
5. 審稿包模板
6. prompt chain
7. Markdown output

等你連續 5～10 天覺得草稿品質穩定，再做：

1. CMS draft
2. 社群 API
3. 自動排程
4. 成效追蹤

---

## 20. 最終產品定義

這個 Agent Skill 的最終型態是：

> 一個每天自動追蹤技術新知、選題、研究、寫稿、查核、產生分發文案，並把完整審稿包交給使用者確認的個人技術媒體代理人。

使用者每天只需做三件事：

1. 看今日選題是否合理。
2. 補上個人觀點或刪掉不適合的內容。
3. 批准發布。

成功時，這個系統會讓使用者在不被每日寫作壓垮的情況下，持續累積技術影響力、搜尋流量、社群曝光與潛在合作機會。

