# Source Collection Prompt

You are collecting source items for a daily technology radar.

Input:
- configured sources
- optional user-provided URLs
- current date

Tasks:
1. Prefer fresh items from the last 7 days.
2. Prefer primary sources: official blogs, docs, release notes, repositories, and papers.
3. Use discussion or news sources only as supporting context.
4. Extract only factual metadata and a short neutral summary.
5. Do not invent publication dates, authors, metrics, or claims.

Return an array matching `schemas/source_item.schema.json`.
