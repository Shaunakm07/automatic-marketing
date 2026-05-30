"""
BlogAgent — writes a full technical blog post from a research digest.

The post is written for Amphora's website blog (amphorabrain.com).
Target audience: ML engineers and curious tech-adjacent readers.
Format: Markdown, ~800–1200 words.
"""

from agents.base import run_agent
from config.strategy import BRAND_VOICE, COMPANY_DESCRIPTION


SYSTEM_PROMPT = f"""
You are the head of content at Amphora, a neuroscience AI company.

{COMPANY_DESCRIPTION}

Brand voice:
{BRAND_VOICE}

You write technical blog posts for amphorabrain.com.
Target reader: an ML engineer or technically curious person who has heard of
fine-tuning and LLMs but does not know neuroscience jargon.

Rules:
- Open with a concrete result or provocative fact — never "In this post, we..."
- Use H2 subheadings (##) sparingly — only when a section genuinely needs separation
- No bullet list walls — prefer short paragraphs
- Bold sparingly, only for truly key terms/numbers
- End with a clear "what's next" or open question that invites comment
- Length: 800–1200 words
- Return raw Markdown only — no front matter, no HTML
""".strip()


def write_blog_post(digest: dict, extra_context: str = "") -> str:
    """
    Write a full blog post from a research digest dict.
    Returns raw Markdown text.
    """
    user_message = f"""
Write a blog post based on this research digest.

Experiment: {digest['experiment_name']}
One-liner: {digest['one_liner']}
Headline stat: {digest['headline_stat']}

Key findings:
{chr(10).join(f'- {f}' for f in digest['key_findings'])}

Narrative:
{digest['narrative']}

Content angles available (pick the best one or blend two):
{chr(10).join(f'- {a}' for a in digest['content_angles'])}

{('Additional context:\n' + extra_context) if extra_context else ''}

Write the full blog post in Markdown.
""".strip()

    return run_agent(SYSTEM_PROMPT, user_message, max_tokens=3000)


def write_blog_title(digest: dict) -> str:
    """Generate 3 candidate titles and return the best one."""
    user_message = f"""
Write 3 candidate blog post titles for this result:
{digest['one_liner']}
Headline stat: {digest['headline_stat']}

Rules: no clickbait, no question marks, under 70 characters, accurate.
Return ONLY a JSON array of 3 strings, e.g.: ["Title A", "Title B", "Title C"]
""".strip()

    import json
    raw = run_agent(SYSTEM_PROMPT, user_message, max_tokens=200)
    titles = json.loads(raw)
    return titles[0]
