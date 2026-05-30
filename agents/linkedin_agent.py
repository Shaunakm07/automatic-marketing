"""
LinkedInAgent — writes LinkedIn posts for Amphora.

Reads the content strategy (pillar rotation, brand voice) and produces
a ready-to-publish post. The post is ~1200 characters, ends with a
question, and uses no markdown formatting.
"""

import json
from agents.base import run_agent
from config.strategy import (
    BRAND_VOICE, COMPANY_DESCRIPTION,
    CONTENT_PILLARS, PILLAR_ROTATION, HASHTAGS,
    LINKEDIN_POST_CONSTRAINTS,
)


SYSTEM_PROMPT = f"""
You are the LinkedIn content strategist for Amphora.

{COMPANY_DESCRIPTION}

Brand voice:
{BRAND_VOICE}

LinkedIn post rules:
- No markdown — no asterisks, no bold, no headers
- Plain text only — line breaks for rhythm are fine
- Max {LINKEDIN_POST_CONSTRAINTS['max_chars']} characters
  (ideal: {LINKEDIN_POST_CONSTRAINTS['ideal_chars']})
- First line is the hook — it must work as a standalone sentence that
  makes someone stop scrolling
- Add a blank line after the hook
- End with a genuine question that invites engagement
- Emojis: none
- Return only the post text — no commentary, no labels
""".strip()


def _pillar_for_rotation(recent_pillars: list[str]) -> str:
    """Pick the next pillar based on what was posted recently."""
    if not recent_pillars:
        return PILLAR_ROTATION[0]
    for pillar in PILLAR_ROTATION:
        if pillar not in recent_pillars[-2:]:
            return pillar
    return PILLAR_ROTATION[0]


def write_post(
    pillar:          str,
    source_material: str,
    recent_posts:    list[str] | None = None,
) -> str:
    """
    Write a single LinkedIn post.

    Args:
        pillar:          one of the PILLAR IDs from strategy.py
        source_material: research digest, blog excerpt, or free-text context
        recent_posts:    last 3–5 post texts (to avoid repetition)

    Returns:
        Post text ready to publish (including hashtags at the end).
    """
    pillar_info = next(p for p in CONTENT_PILLARS if p["id"] == pillar)
    tags        = " ".join(HASHTAGS.get(pillar, []))

    recent_context = ""
    if recent_posts:
        recent_context = "\n\nRecent posts (do NOT repeat these angles or hooks):\n" + \
                         "\n---\n".join(recent_posts[-3:])

    user_message = f"""
Write a LinkedIn post for Amphora.

Content pillar: {pillar_info['name']}
Pillar description: {pillar_info['description']}
Tone: {pillar_info['tone']}
Example hook style: "{pillar_info['example_hook']}"

Source material:
{source_material}
{recent_context}

After the post body, add exactly this on a new line:
{tags}

Write the post now.
""".strip()

    return run_agent(SYSTEM_PROMPT, user_message, max_tokens=800)


def generate_post_queue(
    digest:          dict,
    recent_pillars:  list[str] | None = None,
    n_posts:         int = 3,
) -> list[dict]:
    """
    Generate n_posts LinkedIn posts from a research digest, cycling through pillars.
    Returns list of {"pillar": str, "text": str}.
    """
    recent = recent_pillars or []
    posts  = []

    source = (
        f"Experiment: {digest['experiment_name']}\n"
        f"Headline stat: {digest['headline_stat']}\n"
        f"One-liner: {digest['one_liner']}\n\n"
        f"Key findings:\n" + "\n".join(f"- {f}" for f in digest["key_findings"]) +
        f"\n\nNarrative:\n{digest['narrative']}"
    )

    for i in range(n_posts):
        pillar    = _pillar_for_rotation(recent)
        post_text = write_post(pillar=pillar, source_material=source,
                               recent_posts=[p["text"] for p in posts])
        posts.append({"pillar": pillar, "text": post_text})
        recent.append(pillar)

    return posts
