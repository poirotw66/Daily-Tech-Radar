# Fact Check Prompt

Review the article draft.

Check:
1. Which concrete claims require sources?
2. Which statements are interpretations and should be labeled as such?
3. Are dates, product names, company names, repository names, paper names, and technical terms correct?
4. Is there any overclaiming?
5. Is there any confidential or sensitive workplace information?
6. Are there unsupported business, legal, regulatory, financial, or technology predictions?

Return JSON with:
- fact_check_status: pass | needs_revision | fail
- issues
- claim_source_table
- safe_to_review

If there are high-severity issues, mark `safe_to_review` false.
