"""
SlideshowAgent — generates a LinkedIn carousel from the latest trend report.

Each slide connects a trending AI/ML/neuro story back to Amphora's mission.
Output is structured slide JSON + a self-contained HTML preview suitable
for printing to PDF and uploading as a LinkedIn carousel.

Slide structure (7 slides):
  1. Hook       — bold statement pegged to the day's top viral angle
  2-4. The news — trending topics reframed through Amphora's lens
  5. Synthesis  — the pattern connecting all three stories
  6. Amphora    — what we're building and why it's the answer
  7. CTA        — follow / visit / engage
"""

import json
from agents.base import run_agent
from config.strategy import BRAND_VOICE, COMPANY_DESCRIPTION


SYSTEM_PROMPT = f"""
You are Amphora's creative director, writing LinkedIn carousel slides.

{COMPANY_DESCRIPTION}

Brand voice:
{BRAND_VOICE}

Carousel rules:
- Each slide must work standalone — someone stops scrolling on any slide and still gets value.
- Slide 1 hook must be a single bold sentence that creates a pattern interrupt.
- Slides 2-4 each cover one trending story — lead with the specific fact or title, then pivot to what it reveals.
- Slide 5 synthesises what slides 2-4 have in common, setting up Amphora's angle.
- Slide 6 states Amphora's position specifically — name the technology (TRIBE v2, Broca's area, fMRI prediction).
- Slide 7 is a simple CTA — no more than 2 sentences.
- Headline: max 10 words, punchy.
- Body: max 40 words per slide — short sentences, no filler.
- visual_note: one sentence describing the ideal image or graphic for this slide.
- Return ONLY valid JSON — no markdown fences, no commentary.
""".strip()


def generate_slides(trend_report: dict) -> dict:
    """
    Generate a 7-slide LinkedIn carousel from a trend report.

    Returns:
    {{
      "title":  str,                  # carousel title for internal reference
      "slides": [
        {{
          "number":       int,
          "type":         str,        # hook | trend | synthesis | amphora | cta
          "headline":     str,
          "body":         str,
          "visual_note":  str,
          "trending_peg": str | null  # the exact HN/ArXiv/HF item this references
        }}
      ],
      "hashtags": [str]
    }}
    """
    summary   = trend_report.get("summary", "")
    topics    = trend_report.get("trending_topics", [])[:3]
    angles    = trend_report.get("viral_angles", [])
    top_angle = angles[0] if angles else {}
    hashtags  = trend_report.get("recommended_hashtags", [])[:5]

    topics_block = "\n".join(
        f"  {i+1}. [{t.get('momentum','').upper()}] {t.get('topic','')} — {t.get('amphora_relevance','')}"
        for i, t in enumerate(topics)
    )

    top_hook = top_angle.get("hook", "")
    top_peg  = top_angle.get("trending_peg", "")

    user_message = f"""
Today's trend summary:
{summary}

Top 3 trending topics to cover (slides 2-4):
{topics_block}

Top viral hook for slide 1:
"{top_hook}"
(pegged to: {top_peg})

Produce a 7-slide LinkedIn carousel as JSON with exactly this structure:
{{
  "title": "<internal carousel title, e.g. 'AI Trust Crisis — June 2026'>",
  "slides": [
    {{
      "number": 1,
      "type": "hook",
      "headline": "<max 10 words — the pattern interrupt>",
      "body": "<max 40 words — expand the hook, create urgency>",
      "visual_note": "<one sentence: ideal image or graphic for this slide>",
      "trending_peg": "<the exact story this hooks onto, or null>"
    }},
    {{
      "number": 2,
      "type": "trend",
      "headline": "<max 10 words>",
      "body": "<max 40 words — the specific fact + what it reveals>",
      "visual_note": "<one sentence>",
      "trending_peg": "<exact source item>"
    }},
    {{
      "number": 3,
      "type": "trend",
      "headline": "<max 10 words>",
      "body": "<max 40 words>",
      "visual_note": "<one sentence>",
      "trending_peg": "<exact source item>"
    }},
    {{
      "number": 4,
      "type": "trend",
      "headline": "<max 10 words>",
      "body": "<max 40 words>",
      "visual_note": "<one sentence>",
      "trending_peg": "<exact source item>"
    }},
    {{
      "number": 5,
      "type": "synthesis",
      "headline": "<max 10 words — the common thread>",
      "body": "<max 40 words — what all three stories have in common, the problem statement>",
      "visual_note": "<one sentence>",
      "trending_peg": null
    }},
    {{
      "number": 6,
      "type": "amphora",
      "headline": "<max 10 words — Amphora's specific answer>",
      "body": "<max 40 words — name the technology: TRIBE v2, Broca's area fine-tuning, fMRI prediction. Be concrete.>",
      "visual_note": "<one sentence — brain scan imagery, neural activation maps, etc.>",
      "trending_peg": null
    }},
    {{
      "number": 7,
      "type": "cta",
      "headline": "Follow Amphora",
      "body": "<max 2 sentences — invite engagement or direct to amphorabrain.com>",
      "visual_note": "<one sentence>",
      "trending_peg": null
    }}
  ],
  "hashtags": {json.dumps(hashtags)}
}}
""".strip()

    raw_json = run_agent(SYSTEM_PROMPT, user_message, max_tokens=2000)
    return json.loads(raw_json)


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

_SLIDE_COLORS = {
    "hook":        ("#0f0f0f", "#f5f5f5"),   # dark bg, light text
    "trend":       ("#1a1a2e", "#e8e8ff"),   # deep navy, pale blue
    "synthesis":   ("#0d1117", "#c9d1d9"),   # GitHub dark, silver
    "amphora":     ("#0a2540", "#00d4ff"),   # deep blue, electric cyan
    "cta":         ("#1a1a1a", "#ffffff"),   # near-black, white
}

_SLIDE_LABELS = {
    "hook":      "",
    "trend":     "TRENDING",
    "synthesis": "THE PATTERN",
    "amphora":   "AMPHORA",
    "cta":       "",
}


def render_html(slideshow: dict) -> str:
    """Render slide JSON as a self-contained HTML preview (print-to-PDF friendly)."""
    slides_html = ""
    for slide in slideshow.get("slides", []):
        stype     = slide.get("type", "trend")
        bg, fg    = _SLIDE_COLORS.get(stype, ("#111", "#fff"))
        label     = _SLIDE_LABELS.get(stype, "")
        headline  = slide.get("headline", "")
        body      = slide.get("body", "")
        num       = slide.get("number", "")
        peg       = slide.get("trending_peg") or ""
        vis_note  = slide.get("visual_note", "")

        label_html = f'<div class="label">{label}</div>' if label else ""
        peg_html   = f'<div class="peg">⚡ {peg}</div>' if peg else ""
        num_html   = f'<div class="num">{num} / {len(slideshow.get("slides", []))}</div>'

        slides_html += f"""
<div class="slide" style="background:{bg}; color:{fg};">
  {num_html}
  {label_html}
  <div class="headline">{headline}</div>
  <div class="body">{body}</div>
  {peg_html}
  <div class="vis-note">🎨 {vis_note}</div>
</div>
"""

    hashtags = " ".join(slideshow.get("hashtags", []))
    title    = slideshow.get("title", "Amphora Trend Carousel")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #222; padding: 40px 20px; }}
  h1 {{ color: #fff; font-size: 14px; font-weight: 400; opacity: .5;
        margin-bottom: 32px; letter-spacing: .1em; text-transform: uppercase; }}
  .slide {{
    width: 600px; height: 600px; margin: 0 auto 24px;
    border-radius: 12px; padding: 48px;
    display: flex; flex-direction: column; justify-content: space-between;
    page-break-after: always; position: relative;
  }}
  .num {{ font-size: 11px; opacity: .4; letter-spacing: .15em; }}
  .label {{ font-size: 11px; font-weight: 700; letter-spacing: .2em;
            opacity: .6; margin-top: 4px; }}
  .headline {{ font-size: 32px; font-weight: 800; line-height: 1.15;
               margin-top: auto; padding-top: 24px; }}
  .body {{ font-size: 15px; line-height: 1.65; opacity: .85; margin-top: 16px; }}
  .peg {{ font-size: 11px; opacity: .5; margin-top: 16px; font-style: italic; }}
  .vis-note {{ font-size: 11px; opacity: .35; margin-top: 8px; }}
  .hashtags {{ color: #aaa; font-size: 13px; text-align: center;
               margin-top: 32px; width: 600px; margin-left: auto;
               margin-right: auto; }}
  @media print {{
    body {{ background: #fff; padding: 0; }}
    .slide {{ margin: 0; border-radius: 0; width: 100vw; height: 100vh; }}
  }}
</style>
</head>
<body>
<h1>{title}</h1>
{slides_html}
<div class="hashtags">{hashtags}</div>
</body>
</html>"""
