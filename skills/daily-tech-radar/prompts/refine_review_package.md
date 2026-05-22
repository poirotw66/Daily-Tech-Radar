# LLM Review Package Refinement Prompt

You are refining a Daily Tech Radar review package.

Output language:
- Use Traditional Chinese as the main language.
- Keep professional terms in English when they are clearer: Agent, runtime, orchestration, access control, observability, audit trail, human-in-the-loop, workflow, DevTools, LLM, API, MCP.

Tasks:
1. Strengthen the research section using only the provided sources and scaffold.
2. Rewrite the article so it sounds practical, clear, technical, and business-aware.
3. Keep facts separate from interpretation.
4. Add a fact-check table with claim, source, status, and note.
5. Add limitations and risks, especially for enterprise, financial, customer-data, or regulated workflows.
6. Generate LinkedIn, Threads, Facebook group, newsletter, SEO metadata, and a final review checklist.
7. Mark any statement that still needs human confirmation.

Rules:
- Do not invent facts or dates.
- Use `sources[].page_text` when `page_fetch_status` is `ok` (pipeline-fetched full page). Use `raw_summary` only when full-page fetch failed.
- Do not claim you read sources that were not provided in the JSON.
- Do not add confidential workplace examples.
- Do not make investment, legal, or compliance advice.
- If evidence is insufficient, write `需要人工確認`.
- Do not state that the IDE could not fetch the blog due to network timeout unless `page_fetch_status` is `failed` in the input.

Return one complete Markdown review package with these sections:

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
## 13. 發布前 Checklist
```
