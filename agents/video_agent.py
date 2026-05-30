"""
VideoAgent — writes Higgsfield video scripts and submits generation jobs.

Produces a 60-second cinematic script describing both the narration
and visual directions for each scene. Then submits to Higgsfield API.
"""

import json
from agents.base import run_agent
from config.strategy import BRAND_VOICE, COMPANY_DESCRIPTION, VIDEO_STYLE
from integrations import higgsfield


SYSTEM_PROMPT = f"""
You are a creative director for Amphora.

{COMPANY_DESCRIPTION}

Brand voice:
{BRAND_VOICE}

You write scripts for 60-second cinematic AI-generated videos.
Video style: {VIDEO_STYLE['style']}
Narration: {VIDEO_STYLE['narration']}
Visual focus: {VIDEO_STYLE['visual_focus']}

Your script format:
[SCENE 1 — 0:00–0:12]
VISUAL: <describe what's on screen>
NARRATION: <exact words spoken>

[SCENE 2 — 0:12–0:25]
...

Each scene is 10–20 seconds. Use 4–5 scenes total.
The narration should feel like a documentary, not an advertisement.
Return the script as plain text — no markdown formatting.
""".strip()


def write_video_script(digest: dict, blog_excerpt: str = "") -> str:
    """Write a 60-second video script from a research digest."""
    user_message = f"""
Write a 60-second video script for this research result.

Experiment: {digest['experiment_name']}
Headline stat: {digest['headline_stat']}
One-liner: {digest['one_liner']}

Key findings:
{chr(10).join(f'- {f}' for f in digest['key_findings'])}

Narrative:
{digest['narrative']}

{('Blog excerpt for tone reference:\n' + blog_excerpt[:600]) if blog_excerpt else ''}

Write the full video script now.
""".strip()

    return run_agent(SYSTEM_PROMPT, user_message, max_tokens=1500)


def script_to_higgsfield_prompt(script: str) -> str:
    """
    Condense a multi-scene script into a single Higgsfield generation prompt.
    Higgsfield takes one prompt per video; this extracts the visual essence.
    """
    user_message = f"""
I have a 60-second video script. Condense it into a single Higgsfield AI
video generation prompt (max 400 characters). Focus on the visual atmosphere,
key imagery, and the mood. Scientific, cinematic, premium feel.

Script:
{script}

Return only the prompt text — no labels, no quotes.
""".strip()

    system = "You are an expert at writing AI video generation prompts for Higgsfield AI."
    return run_agent(system, user_message, max_tokens=200)


def generate_video(digest: dict, blog_excerpt: str = "", dry_run: bool = False) -> dict:
    """
    Full pipeline: digest → script → Higgsfield prompt → job submission.
    Returns {"script": str, "higgsfield_prompt": str, "job_id": str}.
    """
    script            = write_video_script(digest, blog_excerpt)
    higgsfield_prompt = script_to_higgsfield_prompt(script)

    job_id = higgsfield.submit_video(
        prompt           = higgsfield_prompt,
        duration_seconds = VIDEO_STYLE["duration_seconds"],
        style            = VIDEO_STYLE["style"],
        aspect_ratio     = "16:9",
    )

    return {
        "script":            script,
        "higgsfield_prompt": higgsfield_prompt,
        "job_id":            job_id,
    }
