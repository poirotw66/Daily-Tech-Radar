#!/usr/bin/env python3
"""Prepare an IDE-agent refinement handoff package.

No API key is required. The output prompt is intended for the current IDE
agent/Codex session to execute using local files and conversation context.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def build_prompt(review_package_json: dict, refinement_instructions: str, output_path: Path) -> str:
    return f"""{refinement_instructions}

## IDE Agent Task

You are running inside the user's IDE workspace. Refine the scaffold below and write the final Markdown review package to:

```text
{output_path}
```

Do not call external publishing APIs. Do not require an OpenAI API key.

Use the provided review package JSON, especially each source's `page_text` when `page_fetch_status` is `ok`. Those excerpts were fetched by the daily pipeline (`enrich_primary_sources.py`), not by ad-hoc IDE browsing. Do not claim you read the full web page if `page_fetch_status` is `failed` or `rss_summary` only.

Only mark `需要人工確認` for claims not supported by `page_text` / `raw_summary`. Do not add a disclaimer that the IDE failed to fetch the blog unless the JSON shows `page_fetch_status: failed`.

## Input Review Package JSON

```json
{json.dumps(review_package_json, ensure_ascii=False, indent=2)}
```
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-package-json", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    review_package = json.loads(read_text(args.review_package_json))
    instructions = read_text(args.prompt)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    refined_output = args.output_dir / f"{timestamp}-agent-refined-review-package.md"
    prompt_path = args.output_dir / f"{timestamp}-agent-refinement-task.md"
    metadata_path = args.output_dir / f"{timestamp}-agent-refinement-metadata.json"

    prompt = build_prompt(review_package, instructions, refined_output)
    prompt_path.write_text(prompt, encoding="utf-8")

    metadata = {
        "mode": "ide_agent_handoff",
        "prompt_path": str(prompt_path),
        "output_path": str(refined_output),
        "requires_api_key": False,
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
