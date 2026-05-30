"""
ResearchAgent — reads EXPERIMENT*.md files and produces structured digests.

Output:
  {
    "experiment_name": str,
    "one_liner":       str,          # 1-sentence result summary
    "key_findings":    list[str],    # 3–5 bullet points
    "headline_stat":   str,          # the most quotable number/result
    "narrative":       str,          # 2–3 paragraph plain-language explanation
    "content_angles":  list[str],    # 5 LinkedIn/blog angle ideas
  }
"""

import json
from agents.base import run_agent
from config.strategy import BRAND_VOICE, COMPANY_DESCRIPTION


SYSTEM_PROMPT = f"""
You are the research communications lead for Amphora, a neuroscience AI company.

{COMPANY_DESCRIPTION}

Brand voice:
{BRAND_VOICE}

Your job: read a raw experiment results document and extract a structured digest.
Return ONLY valid JSON matching the schema the user specifies — no markdown fences,
no extra commentary.
""".strip()


def digest_experiment(experiment_name: str, experiment_md: str) -> dict:
    user_message = f"""
Experiment file: {experiment_name}

---
{experiment_md}
---

Extract a structured digest as JSON with exactly these keys:
{{
  "experiment_name": "<name of the experiment>",
  "one_liner": "<single sentence capturing the main result>",
  "key_findings": ["<finding 1>", "<finding 2>", "..."],
  "headline_stat": "<the single most quotable number or result, e.g. '+150% Broca activation'>",
  "narrative": "<2–3 paragraphs explaining what was done and why it matters, no jargon>",
  "content_angles": [
    "<angle 1 — a LinkedIn post angle>",
    "<angle 2>",
    "<angle 3>",
    "<angle 4>",
    "<angle 5>"
  ]
}}

Rules:
- key_findings: 3–5 items, each under 25 words
- headline_stat: a concrete number or comparison, not vague ("significant improvement")
- narrative: accessible to a non-neuroscientist, 150–250 words total
- content_angles: each is a specific angle for a LinkedIn post or blog, not just a topic label
""".strip()

    raw = run_agent(SYSTEM_PROMPT, user_message, max_tokens=2048)
    return json.loads(raw)
