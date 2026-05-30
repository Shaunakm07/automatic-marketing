"""
TrendAgent — analyses what's trending in AI/ML/neuro and generates viral marketing angles.

Input:  raw scraped data from integrations/trend_scraper.py
Output: structured trend report saved to Supabase
"""

import json
from datetime import datetime, timezone

from agents.base import run_agent
from config.strategy import BRAND_VOICE, COMPANY_DESCRIPTION, CONTENT_PILLARS

_PILLAR_IDS = [p["id"] for p in CONTENT_PILLARS]

SYSTEM_PROMPT = f"""
You are Amphora's growth strategist and viral content analyst.

{COMPANY_DESCRIPTION}

Brand voice:
{BRAND_VOICE}

Your job: given today's trending content across HN, Reddit, ArXiv, and Twitter,
identify which themes are gaining momentum, assess their relevance to Amphora,
and produce specific viral content angles Amphora can ride TODAY.

Rules:
- Be specific — name the actual paper, thread, or event. No vague categories.
- Viral angles must have a concrete hook sentence, not a topic label.
- Virality score 1–10: 10 = rare perfect timing, 7 = strong opportunity.
- Return ONLY valid JSON — no markdown fences, no commentary.
""".strip()


def analyse_trends(raw: dict) -> dict:
    """
    Takes output from trend_scraper.fetch_all() and returns a structured trend report.

    Report schema:
    {
      "summary":             str,
      "trending_topics":     [ { topic, sources, momentum, amphora_relevance, angle } ],
      "viral_angles":        [ { hook, pillar, virality_score, why_now, trending_peg } ],
      "recommended_hashtags": [str],
      "competitor_gap":      str,
    }
    (generated_at and sources_used are added by this function before returning.)
    """

    def _titles(items: list[dict], limit: int) -> str:
        return "\n".join(f"  - {i['title']}" for i in items[:limit] if i.get("title"))

    hn_block      = _titles(raw.get("hn",      []), 18)
    reddit_block  = _titles(raw.get("reddit",  []), 18)
    arxiv_block   = _titles(raw.get("arxiv",   []), 12)
    twitter_block = _titles(raw.get("twitter", []),  8)

    sections = [
        f"HACKER NEWS TOP STORIES:\n{hn_block}"     if hn_block      else "",
        f"TOP REDDIT AI/ML POSTS:\n{reddit_block}"  if reddit_block  else "",
        f"RECENT ARXIV PAPERS:\n{arxiv_block}"      if arxiv_block   else "",
        f"TRENDING AI TWEETS:\n{twitter_block}"      if twitter_block else "",
    ]
    data_block = "\n\n".join(s for s in sections if s)

    user_message = f"""
Today's trending content:

{data_block}

Amphora's content pillars: {', '.join(_PILLAR_IDS)}

Produce a trend report as JSON with exactly this structure:
{{
  "summary": "<2-3 sentences on the biggest AI/ML themes trending right now>",
  "trending_topics": [
    {{
      "topic": "<specific topic — name the actual paper/event/thread>",
      "sources": ["<source name>"],
      "momentum": "high|medium|low",
      "amphora_relevance": "<one sentence on why this matters for Amphora>",
      "angle": "<specific content angle Amphora could take>"
    }}
  ],
  "viral_angles": [
    {{
      "hook": "<exact first sentence of the post — concrete, makes you stop scrolling, under 200 chars>",
      "pillar": "<one of: {', '.join(_PILLAR_IDS)}>",
      "virality_score": <1-10>,
      "why_now": "<why this lands harder today than any other day — reference the trend>",
      "trending_peg": "<the exact HN/Reddit/arxiv item or tweet this hooks onto>"
    }}
  ],
  "recommended_hashtags": ["<tag1>", "<tag2>", "..."],
  "competitor_gap": "<one specific thing other AI companies aren't saying that Amphora uniquely can — be concrete>"
}}

Rules:
- trending_topics: 4–6 items
- viral_angles: exactly 5 items, ordered by virality_score descending
- hooks must be ruthlessly specific — no "AI is advancing" generalities
- every viral angle must reference a real thing from today's trends
""".strip()

    raw_json = run_agent(SYSTEM_PROMPT, user_message, max_tokens=2800)
    report = json.loads(raw_json)
    report["generated_at"]  = datetime.now(timezone.utc).isoformat()
    report["sources_used"]  = raw.get("sources_used", [])
    return report
