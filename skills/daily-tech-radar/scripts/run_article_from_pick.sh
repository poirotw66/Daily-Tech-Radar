#!/usr/bin/env bash
# Run enrich + draft + review package after the user picks a candidate topic.
set -euo pipefail

RUN_DATE="${RUN_DATE:-$(date +%Y-%m-%d)}"
CANDIDATE_ID="${CANDIDATE_ID:-}"
INSECURE_SKIP_TLS_VERIFY="${INSECURE_SKIP_TLS_VERIFY:-1}"
PREPARE_AGENT_REFINEMENT="${PREPARE_AGENT_REFINEMENT:-1}"

if [[ -z "${CANDIDATE_ID}" ]]; then
  echo "Set CANDIDATE_ID to the candidate_id from output/candidates/${RUN_DATE}-topic-selection-brief.md" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PY="${PYTHON:-python3}"

TLS=()
if [[ "${INSECURE_SKIP_TLS_VERIFY}" == "1" ]]; then
  TLS=(--insecure-skip-tls-verify)
fi

SCORES="${SKILL_DIR}/output/candidates/${RUN_DATE}-scores.json"
CAND="${SKILL_DIR}/output/candidates/${RUN_DATE}-candidates.json"
NORM="${SKILL_DIR}/data/normalized/${RUN_DATE}-normalized.json"
ENRICHED="${SKILL_DIR}/data/enriched/${RUN_DATE}-normalized-enriched.json"
DRAFT_DIR="${SKILL_DIR}/output/drafts/${RUN_DATE}"
REVIEW_DIR="${SKILL_DIR}/output/review_packages"
REFINE_DIR="${SKILL_DIR}/output/refinements/${RUN_DATE}"

if [[ ! -f "${SCORES}" ]]; then
  echo "Missing scores file: ${SCORES}. Run run_daily_radar.sh (discover) first." >&2
  exit 1
fi

run_step() {
  echo "==> $1"
  shift
  "$@"
}

run_step "Apply user topic pick" "${PY}" "${SCRIPT_DIR}/select_topic.py" \
  --scores "${SCORES}" --candidate-id "${CANDIDATE_ID}"

run_step "Enrich primary source pages" "${PY}" "${SCRIPT_DIR}/enrich_primary_sources.py" \
  --normalized "${NORM}" --candidates "${CAND}" --scores "${SCORES}" \
  --output "${ENRICHED}" "${TLS[@]}"

run_step "Build Traditional Chinese draft package" "${PY}" "${SCRIPT_DIR}/build_draft_package.py" \
  --candidates "${CAND}" --scores "${SCORES}" --sources "${ENRICHED}" \
  --run-date "${RUN_DATE}" --output-dir "${DRAFT_DIR}"

RP_JSON="$(ls -t "${DRAFT_DIR}"/*-review-package.json 2>/dev/null | head -1)"
if [[ -z "${RP_JSON}" ]]; then
  echo "No review-package JSON produced under ${DRAFT_DIR}" >&2
  exit 1
fi

run_step "Build Markdown review package" "${PY}" "${SCRIPT_DIR}/build_review_package.py" \
  "${RP_JSON}" --output "${REVIEW_DIR}"

if [[ "${PREPARE_AGENT_REFINEMENT}" == "1" ]]; then
  run_step "Prepare IDE agent refinement task" "${PY}" "${SCRIPT_DIR}/prepare_agent_refinement.py" \
    --review-package-json "${RP_JSON}" \
    --prompt "${SKILL_DIR}/prompts/refine_review_package.md" \
    --output-dir "${REFINE_DIR}"
fi

run_step "Update topic memory" "${PY}" "${SCRIPT_DIR}/update_topic_memory.py" \
  --scores "${SCORES}" --memory "${SKILL_DIR}/memory/topic_memory.json" --run-date "${RUN_DATE}"

echo ""
echo "Article pipeline complete for ${CANDIDATE_ID} (${RUN_DATE})."
echo "Review package dir: ${REVIEW_DIR}"
echo "Refinement dir: ${REFINE_DIR}"
