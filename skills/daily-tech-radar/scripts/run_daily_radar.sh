#!/usr/bin/env bash
# Daily Tech Radar orchestrator for macOS/Linux (mirrors Run-DailyRadar.ps1).
set -euo pipefail

RUN_DATE="${RUN_DATE:-$(date +%Y-%m-%d)}"
RSS_LIMIT="${RSS_LIMIT:-5}"
ARXIV_LIMIT="${ARXIV_LIMIT:-8}"
GITHUB_LIMIT="${GITHUB_LIMIT:-8}"
GITHUB_DAYS="${GITHUB_DAYS:-30}"
GITHUB_MIN_STARS="${GITHUB_MIN_STARS:-100}"
INSECURE_SKIP_TLS_VERIFY="${INSECURE_SKIP_TLS_VERIFY:-1}"
DISCOVER_ONLY="${DISCOVER_ONLY:-1}"
PREPARE_AGENT_REFINEMENT="${PREPARE_AGENT_REFINEMENT:-0}"
INCLUDE_ARXIV="${INCLUDE_ARXIV:-0}"

if [[ "${DISCOVER_ONLY}" == "1" ]]; then
  PREPARE_AGENT_REFINEMENT=0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PY="${PYTHON:-python3}"

TLS=()
if [[ "${INSECURE_SKIP_TLS_VERIFY}" == "1" ]]; then
  TLS=(--insecure-skip-tls-verify)
fi

SOURCE_DIR="${SKILL_DIR}/data/sources"
NORMALIZED_DIR="${SKILL_DIR}/data/normalized"
ENRICHED_DIR="${SKILL_DIR}/data/enriched"
BRIEF_DIR="${SKILL_DIR}/output/source_briefs"
CANDIDATE_DIR="${SKILL_DIR}/output/candidates"
DRAFT_DIR="${SKILL_DIR}/output/drafts"
REVIEW_DIR="${SKILL_DIR}/output/review_packages"
REFINE_DIR="${SKILL_DIR}/output/refinements"
HEALTH_DIR="${SKILL_DIR}/output/source_health"
LOG_DIR="${SKILL_DIR}/output/logs"
MEMORY_DIR="${SKILL_DIR}/memory"

mkdir -p "${SOURCE_DIR}" "${NORMALIZED_DIR}" "${ENRICHED_DIR}" \
  "${BRIEF_DIR}" "${CANDIDATE_DIR}" "${DRAFT_DIR}/${RUN_DATE}" \
  "${REVIEW_DIR}" "${REFINE_DIR}/${RUN_DATE}" "${HEALTH_DIR}" "${LOG_DIR}" "${MEMORY_DIR}"

RSS_OUT="${SOURCE_DIR}/${RUN_DATE}-rss.json"
ARXIV_OUT="${SOURCE_DIR}/${RUN_DATE}-arxiv.json"
GITHUB_OUT="${SOURCE_DIR}/${RUN_DATE}-github.json"
RAW_OUT="${SOURCE_DIR}/${RUN_DATE}-raw.json"
NORM_OUT="${NORMALIZED_DIR}/${RUN_DATE}-normalized.json"
ENRICHED_OUT="${ENRICHED_DIR}/${RUN_DATE}-enriched-sources.json"
BRIEF_OUT="${BRIEF_DIR}/${RUN_DATE}-source-brief.md"
CAND_OUT="${CANDIDATE_DIR}/${RUN_DATE}-candidates.json"
SCORES_OUT="${CANDIDATE_DIR}/${RUN_DATE}-scores.json"
TOPIC_BRIEF="${CANDIDATE_DIR}/${RUN_DATE}-topic-selection-brief.md"
DRAFT_OUT="${DRAFT_DIR}/${RUN_DATE}"
MEMORY="${MEMORY_DIR}/topic_memory.json"
HEALTH_OUT="${HEALTH_DIR}/${RUN_DATE}-source-health.md"

run_step() {
  echo "==> $1"
  shift
  "$@"
}

run_step "Fetch RSS" "${PY}" "${SCRIPT_DIR}/fetch_rss_from_config.py" \
  --config "${SKILL_DIR}/config/rss_sources.yaml" --limit "${RSS_LIMIT}" \
  "${TLS[@]}" --output "${RSS_OUT}"

if [[ "${INCLUDE_ARXIV}" == "1" ]]; then
  run_step "Fetch arXiv" "${PY}" "${SCRIPT_DIR}/fetch_arxiv.py" \
    --category cs.AI --category cs.CL --category cs.LG \
    --max-results "${ARXIV_LIMIT}" "${TLS[@]}" --output "${ARXIV_OUT}"
else
  echo '[]' > "${ARXIV_OUT}"
  echo "==> Fetch arXiv skipped (set INCLUDE_ARXIV=1 to enable)"
fi

run_step "Fetch GitHub repos" "${PY}" "${SCRIPT_DIR}/fetch_github_repos.py" \
  --days "${GITHUB_DAYS}" --min-stars "${GITHUB_MIN_STARS}" --per-page "${GITHUB_LIMIT}" \
  "${TLS[@]}" --output "${GITHUB_OUT}"

PAGE_WATCH_OUT="${SOURCE_DIR}/${RUN_DATE}-page-watch.json"
PAGE_WATCH_BRIEF="${SKILL_DIR}/output/page_watch/${RUN_DATE}-page-watch-brief.md"
mkdir -p "${SKILL_DIR}/output/page_watch"
run_step "Watch web pages for updates" "${PY}" "${SCRIPT_DIR}/watch_pages.py" \
  --config "${SKILL_DIR}/config/page_watch.yaml" \
  --run-date "${RUN_DATE}" \
  --output-items "${PAGE_WATCH_OUT}" \
  --output-brief "${PAGE_WATCH_BRIEF}" \
  "${TLS[@]}"
if [[ ! -s "${PAGE_WATCH_OUT}" ]]; then
  echo '[]' > "${PAGE_WATCH_OUT}"
fi

run_step "Merge sources" "${PY}" "${SCRIPT_DIR}/merge_sources.py" \
  "${RSS_OUT}" "${ARXIV_OUT}" "${GITHUB_OUT}" "${PAGE_WATCH_OUT}" --output "${RAW_OUT}"

run_step "Normalize sources" "${PY}" "${SCRIPT_DIR}/normalize_sources.py" \
  "${RAW_OUT}" --output "${NORM_OUT}"

run_step "Build source brief" "${PY}" "${SCRIPT_DIR}/build_source_brief.py" \
  "${NORM_OUT}" --run-date "${RUN_DATE}" --output "${BRIEF_OUT}"

run_step "Generate topic candidates" "${PY}" "${SCRIPT_DIR}/generate_candidates_from_sources.py" \
  "${NORM_OUT}" --limit 5 --topic-memory "${MEMORY}" --output "${CAND_OUT}"

SCORE_EXTRA=()
if [[ "${DISCOVER_ONLY}" == "1" ]]; then
  SCORE_EXTRA=(--recommendation-only)
fi

run_step "Score topic candidates" "${PY}" "${SCRIPT_DIR}/score_topics.py" \
  "${CAND_OUT}" --scoring "${SKILL_DIR}/config/scoring.yaml" --output "${SCORES_OUT}" "${SCORE_EXTRA[@]}"

run_step "Build topic selection brief" "${PY}" "${SCRIPT_DIR}/build_topic_selection_brief.py" \
  "${SCORES_OUT}" --sources "${NORM_OUT}" --output "${TOPIC_BRIEF}"

run_step "Build source health report" "${PY}" "${SCRIPT_DIR}/build_source_health_report.py" \
  --logs-dir "${LOG_DIR}" --limit 30 --output "${HEALTH_OUT}"

if [[ "${DISCOVER_ONLY}" == "1" ]]; then
  echo ""
  echo "Discover-only run complete (no draft). Review:"
  echo "  Source brief: ${BRIEF_OUT}"
  echo "  Topic selection brief: ${TOPIC_BRIEF}"
  echo "  Page watch brief: ${PAGE_WATCH_BRIEF}"
  echo "Then pick a candidate_id and run:"
  echo "  CANDIDATE_ID=<id> ./scripts/run_article_from_pick.sh"
  exit 0
fi

run_step "Update topic memory" "${PY}" "${SCRIPT_DIR}/update_topic_memory.py" \
  --scores "${SCORES_OUT}" --memory "${MEMORY}" --run-date "${RUN_DATE}"

run_step "Enrich primary source pages" "${PY}" "${SCRIPT_DIR}/enrich_primary_sources.py" \
  --normalized "${NORM_OUT}" --candidates "${CAND_OUT}" --scores "${SCORES_OUT}" \
  --output "${ENRICHED_OUT}" "${TLS[@]}"

run_step "Build Traditional Chinese draft package" "${PY}" "${SCRIPT_DIR}/build_draft_package.py" \
  --candidates "${CAND_OUT}" --scores "${SCORES_OUT}" --sources "${ENRICHED_OUT}" \
  --run-date "${RUN_DATE}" --output-dir "${DRAFT_OUT}"

RP_JSON="$(ls -t "${DRAFT_OUT}"/*-review-package.json 2>/dev/null | head -1)"
if [[ -n "${RP_JSON}" ]]; then
  run_step "Build Markdown review package" "${PY}" "${SCRIPT_DIR}/build_review_package.py" \
    "${RP_JSON}" --output "${REVIEW_DIR}"
  if [[ "${PREPARE_AGENT_REFINEMENT}" == "1" ]]; then
    run_step "Prepare IDE agent refinement task" "${PY}" "${SCRIPT_DIR}/prepare_agent_refinement.py" \
      --review-package-json "${RP_JSON}" \
      --prompt "${SKILL_DIR}/prompts/refine_review_package.md" \
      --output-dir "${REFINE_DIR}/${RUN_DATE}"
  fi
fi

echo ""
echo "Daily Tech Radar full pipeline complete."
echo "Source brief: ${BRIEF_OUT}"
echo "Topic selection brief: ${TOPIC_BRIEF}"
echo "Enriched sources: ${ENRICHED_OUT}"
echo "Draft dir: ${DRAFT_OUT}"
echo "Refinement dir: ${REFINE_DIR}/${RUN_DATE}"
echo "Page watch brief: ${PAGE_WATCH_BRIEF}"
echo "Next: ask the IDE agent to run the latest refinement task, or refine the Markdown package manually."
