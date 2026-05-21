# Deduplicate Sources Prompt

You are clustering source items into topic clusters.

Tasks:
1. Merge items that describe the same announcement, release, paper, repo, security issue, or workflow trend.
2. Choose the most authoritative primary source as `primary_source`.
3. Keep discussion/news items as `supporting_sources`.
4. Assign a `detected_angle`.
5. Preserve uncertainties when two items might not describe the same event.

Return topic clusters as JSON. Do not write prose outside JSON.
