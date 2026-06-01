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
# Research digest → slides (used by orchestrator instead of LinkedIn posts)
# ---------------------------------------------------------------------------

_RESEARCH_SYSTEM_PROMPT = f"""
You are Amphora's creative director, writing LinkedIn carousel slides about a research experiment.

{COMPANY_DESCRIPTION}

Brand voice:
{BRAND_VOICE}

Carousel rules:
- Each slide must work standalone.
- Slide 1: the headline stat as a pattern interrupt — one bold sentence.
- Slides 2-4: one key finding each — lead with the specific result, then what it means.
- Slide 5: the bigger implication — why this finding matters for the future of AI.
- Slide 6: Amphora's position — name TRIBE v2, Broca's area, fMRI prediction specifically.
- Slide 7: CTA — two sentences max.
- Headline: max 10 words. Body: max 40 words. No filler.
- visual_note: one sentence for the ideal background image.
- Return ONLY valid JSON — no markdown fences, no commentary.
""".strip()


def generate_slides_from_digest(digest: dict) -> dict:
    """
    Generate a 7-slide carousel from a research experiment digest.
    Used by the orchestrator in place of LinkedIn posts.
    """
    findings_block = "\n".join(f"  {i+1}. {f}" for i, f in enumerate(digest.get("key_findings", [])[:3]))

    user_message = f"""
Research experiment: {digest['experiment_name']}
Headline stat: {digest['headline_stat']}
One-liner: {digest['one_liner']}

Key findings (use for slides 2-4):
{findings_block}

Narrative:
{digest['narrative'][:600]}

Produce a 7-slide LinkedIn carousel as JSON:
{{
  "title": "<experiment name + short descriptor>",
  "slides": [
    {{"number": 1, "type": "hook",      "headline": "<max 10 words — the headline stat as a pattern interrupt>",       "body": "<max 40 words>", "visual_note": "<one sentence>", "trending_peg": null}},
    {{"number": 2, "type": "finding",   "headline": "<max 10 words — key finding 1>",  "body": "<max 40 words>", "visual_note": "<one sentence>", "trending_peg": null}},
    {{"number": 3, "type": "finding",   "headline": "<max 10 words — key finding 2>",  "body": "<max 40 words>", "visual_note": "<one sentence>", "trending_peg": null}},
    {{"number": 4, "type": "finding",   "headline": "<max 10 words — key finding 3>",  "body": "<max 40 words>", "visual_note": "<one sentence>", "trending_peg": null}},
    {{"number": 5, "type": "synthesis", "headline": "<max 10 words — the bigger implication>", "body": "<max 40 words>", "visual_note": "<one sentence>", "trending_peg": null}},
    {{"number": 6, "type": "amphora",   "headline": "<max 10 words — Amphora's specific answer>", "body": "<max 40 words — name TRIBE v2, Broca's area, fMRI>", "visual_note": "<one sentence — brain scan imagery>", "trending_peg": null}},
    {{"number": 7, "type": "cta",       "headline": "Follow Amphora", "body": "<max 2 sentences>", "visual_note": "<one sentence>", "trending_peg": null}}
  ],
  "hashtags": ["#BrainAI", "#fMRI", "#NLP", "#GenerativeAI", "#Neuroscience"]
}}
""".strip()

    raw_json = run_agent(_RESEARCH_SYSTEM_PROMPT, user_message, max_tokens=2000)
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


def render_html(slideshow: dict, images: dict[int, str] | None = None) -> str:
    """
    Render slide JSON as a self-contained HTML preview (print-to-PDF friendly).

    images: optional {slide_number: base64_data_uri} from image_gen.generate_all().
            When present, each slide's visual_note image is used as a background
            with a dark overlay for text readability.
    """
    images    = images or {}
    n_slides  = len(slideshow.get("slides", []))
    slides_html = ""

    for slide in slideshow.get("slides", []):
        stype    = slide.get("type", "trend")
        bg, fg   = _SLIDE_COLORS.get(stype, ("#111", "#fff"))
        label    = _SLIDE_LABELS.get(stype, "")
        headline = slide.get("headline", "")
        body     = slide.get("body", "")
        num      = slide.get("number", "")
        peg      = slide.get("trending_peg") or ""

        label_html = f'<div class="label">{label}</div>' if label else ""
        peg_html   = f'<div class="peg">⚡ {peg}</div>'  if peg   else ""
        num_html   = f'<div class="num">{num} / {n_slides}</div>'

        # Background: generated image (with overlay) or solid color fallback
        img_uri = images.get(num, "")
        if img_uri:
            bg_style  = f"background-image: url('{img_uri}'); background-size: cover; background-position: center;"
            overlay   = '<div class="img-overlay"></div>'
        else:
            bg_style = f"background: {bg};"
            overlay  = ""

        slides_html += f"""
<div class="slide" style="{bg_style} color:{fg};">
  {overlay}
  <div class="content">
    {num_html}
    {label_html}
    <div class="headline">{headline}</div>
    <div class="body-text">{body}</div>
    {peg_html}
  </div>
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
         background: #111; padding: 40px 20px; }}
  h1 {{ color: #fff; font-size: 13px; font-weight: 400; opacity: .4;
        margin-bottom: 32px; letter-spacing: .12em; text-transform: uppercase; }}
  .slide {{
    width: 600px; height: 600px; margin: 0 auto 24px;
    border-radius: 12px; overflow: hidden;
    position: relative; page-break-after: always;
  }}
  .img-overlay {{
    position: absolute; inset: 0;
    background: linear-gradient(160deg, rgba(0,0,0,.55) 0%, rgba(0,0,0,.35) 100%);
    z-index: 1;
  }}
  .content {{
    position: relative; z-index: 2;
    height: 100%; padding: 44px;
    display: flex; flex-direction: column; justify-content: space-between;
  }}
  .num {{ font-size: 11px; opacity: .5; letter-spacing: .15em; color: #fff; }}
  .label {{ font-size: 10px; font-weight: 800; letter-spacing: .25em;
            opacity: .7; margin-top: 4px; color: #fff;
            text-transform: uppercase; }}
  .headline {{ font-size: 30px; font-weight: 900; line-height: 1.12;
               margin-top: auto; padding-top: 20px; color: #fff;
               text-shadow: 0 2px 12px rgba(0,0,0,.6); }}
  .body-text {{ font-size: 14px; line-height: 1.6; opacity: .9;
                margin-top: 14px; color: #f0f0f0;
                text-shadow: 0 1px 6px rgba(0,0,0,.5); }}
  .peg {{ font-size: 10px; opacity: .55; margin-top: 14px;
          font-style: italic; color: #fff; }}
  .hashtags {{ color: #777; font-size: 12px; text-align: center;
               margin-top: 28px; width: 600px; margin-left: auto;
               margin-right: auto; line-height: 1.8; }}
  @media print {{
    body {{ background: #000; padding: 0; }}
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
