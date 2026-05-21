# Topic Candidate Prompt

You are generating daily article candidates for a personal technical media site.

Positioning:
- AI engineering
- agentic coding and vibe coding
- developer tools
- automation workflows
- FinTech AI applications

Generate 3-5 candidate topics from the topic clusters.

Prioritize topics that:
- can become a practical article, not just a news translation
- have a primary source
- can show a distinct judgment angle
- can connect to engineering, product, automation, small-business, enterprise, or financial-service workflows

Reject topics that:
- are funding-only, rumor-only, or social hype
- lack practical implications
- require confidential workplace details

Return JSON matching `schemas/topic_candidate.schema.json` as an array.
