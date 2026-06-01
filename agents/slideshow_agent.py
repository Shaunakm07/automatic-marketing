"""
SlideshowAgent — generates a LinkedIn carousel from the latest trend report.

Follows the 6 rules from the carousel system:
  Rule 01: Cover has one job — stop the scroll. Max 8 words. Promise or number.
  Rule 02: Slide 2 confirms the hook. Opens the problem, raises stakes.
  Rule 03: Every slide works as a screenshot on its own. One idea, no context needed.
  Rule 04: One slide is save-worthy — a framework, stat, or line sharp enough to quote.
  Rule 05: AI handles structure, voice stays human.
  Rule 06: Caption is the second post. Ends with one comment trigger.

Output: slide JSON + LinkedIn caption + self-contained HTML preview.
"""

import json
from agents.base import run_agent
from config.strategy import BRAND_VOICE, COMPANY_DESCRIPTION


def _parse_json(raw: str) -> dict:
    """Parse JSON from agent output, stripping markdown fences if present."""
    raw = raw.strip()
    if not raw:
        raise ValueError("Agent returned an empty response")
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(raw.strip())


SYSTEM_PROMPT = f"""
You are Amphora's carousel architect, writing LinkedIn carousels that follow 6 non-negotiable rules.

{COMPANY_DESCRIPTION}

Brand voice:
{BRAND_VOICE}

THE 6 RULES — follow every one, no exceptions:

Rule 01 — COVER STOPS THE SCROLL.
Slide 1 headline: max 8 words. A promise or a number. Never a topic label.
It competes with everything on the feed — reels, friends, ads. One job only.

Rule 02 — SLIDE 2 CONFIRMS THE HOOK OR THEY LEAVE.
This is the highest drop-off point. Open the problem immediately.
Name what it's costing them, the mistake they're making, or the gap they're in.
Reader must think "this is worth my time" before finishing the slide.

Rule 03 — EVERY SLIDE WORKS AS A STANDALONE SCREENSHOT.
Each slide must make complete sense with zero context from the surrounding slides.
One idea per slide. No "and that's why..." or "the third reason is..."
A slide that needs context is a slide that can't be shared.

Rule 04 — ONE SLIDE MUST BE SAVE-WORTHY.
Build one slide as the keeper: a sharp stat, a framework, a fill-in-the-blank,
or a line so precise they'll quote it. Flag it with "save_worthy": true.
Saves beat reach — the algorithm rewards them most.

Rule 05 — STRUCTURE CARRIES THE NARRATIVE.
Arc: Cover → Confirm → Build → Climax → CTA. Energy rises, then resolves.
The structure is AI's job. The voice is Amphora's.

Rule 06 — CAPTION IS THE SECOND POST.
The caption adds value the carousel didn't have. It opens with a sharp claim,
adds one piece of context, stays under 150 words, and ends with exactly:
"Comment [KEYWORD] and I'll send it to you."

Output rules:
- Headline: max 8 words (cover), max 10 words (other slides).
- Body: max 40 words per slide. Short sentences. No filler. No hustle language.
- visual_note: one sentence — the background image concept. Pure visual, NO TEXT IN IMAGE.
- Return ONLY valid JSON — no markdown fences, no commentary.
""".strip()


def generate_slides(trend_report: dict) -> dict:
    """
    Generate a 7-slide LinkedIn carousel + caption from a trend report.

    Returns schema:
    {{
      "title":    str,
      "caption":  str,   # LinkedIn caption — the second post (Rule 06)
      "slides": [
        {{
          "number":      int,
          "type":        str,   # cover | confirm | build | save_worthy | climax | cta
          "headline":    str,
          "body":        str,
          "visual_note": str,
          "save_worthy": bool,
          "trending_peg": str | null
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

Top 3 trending topics (for slides 3-5):
{topics_block}

Strongest viral hook available for the cover:
"{top_hook}"
(pegged to: {top_peg})

Produce a 7-slide carousel + caption as JSON:
{{
  "title": "<carousel title for internal reference>",
  "caption": "<LinkedIn caption — opens with sharp claim, adds context carousel didn't have, under 150 words, ends with 'Comment BRAINAI and I\\'ll send it to you.'>",
  "slides": [
    {{
      "number": 1,
      "type": "cover",
      "headline": "<MAX 8 WORDS — promise or number, stops scroll, never a topic label>",
      "body": "<max 40 words — expand the promise, make it impossible to swipe past>",
      "visual_note": "<pure visual background concept — no text in image>",
      "save_worthy": false,
      "trending_peg": "<exact item this hooks onto>"
    }},
    {{
      "number": 2,
      "type": "confirm",
      "headline": "<max 10 words — open the problem, raise the stakes>",
      "body": "<max 40 words — name what it's costing them or the gap they're in. Reader thinks: this is worth my time>",
      "visual_note": "<pure visual background concept — no text in image>",
      "save_worthy": false,
      "trending_peg": null
    }},
    {{
      "number": 3,
      "type": "build",
      "headline": "<max 10 words — specific trend, name the paper/event/thread>",
      "body": "<max 40 words — the specific fact + what it reveals. Works cold with no context>",
      "visual_note": "<pure visual background concept — no text in image>",
      "save_worthy": false,
      "trending_peg": "<exact source item>"
    }},
    {{
      "number": 4,
      "type": "build",
      "headline": "<max 10 words>",
      "body": "<max 40 words — standalone, one idea, no 'and that's why'>",
      "visual_note": "<pure visual background concept — no text in image>",
      "save_worthy": false,
      "trending_peg": "<exact source item>"
    }},
    {{
      "number": 5,
      "type": "save_worthy",
      "headline": "<max 10 words — a line sharp enough to quote or a framework header>",
      "body": "<max 40 words — a stat, framework, fill-in-the-blank, or line so precise they screenshot it>",
      "visual_note": "<pure visual background concept — no text in image>",
      "save_worthy": true,
      "trending_peg": null
    }},
    {{
      "number": 6,
      "type": "climax",
      "headline": "<max 10 words — Amphora's specific answer to everything above>",
      "body": "<max 40 words — name TRIBE v2, Broca's area fine-tuning, fMRI prediction. Concrete. This is the payoff.>",
      "visual_note": "<pure visual background concept — brain scan, neural activation. No text in image>",
      "save_worthy": false,
      "trending_peg": null
    }},
    {{
      "number": 7,
      "type": "cta",
      "headline": "<max 8 words — one action + one reward>",
      "body": "<max 2 sentences — one clear action, one specific reward. Comment trigger.>",
      "visual_note": "<pure visual background concept — no text in image>",
      "save_worthy": false,
      "trending_peg": null
    }}
  ],
  "hashtags": {json.dumps(hashtags)}
}}
""".strip()

    raw_json = run_agent(SYSTEM_PROMPT, user_message, max_tokens=4096)
    return _parse_json(raw_json)


# ---------------------------------------------------------------------------
# Research digest → slides (used by orchestrator instead of LinkedIn posts)
# ---------------------------------------------------------------------------

def generate_slides_from_digest(digest: dict) -> dict:
    """
    Generate a 7-slide carousel + caption from a research experiment digest.
    Uses the same SYSTEM_PROMPT (6 rules) as the trend carousel.
    """
    findings_block = "\n".join(f"  {i+1}. {f}" for i, f in enumerate(digest.get("key_findings", [])[:3]))

    user_message = f"""
Research experiment: {digest['experiment_name']}
Headline stat: {digest['headline_stat']}
One-liner: {digest['one_liner']}

Key findings (use for build slides):
{findings_block}

Narrative:
{digest['narrative'][:600]}

Produce a 7-slide carousel following the 6 rules. The "trending_peg" for each slide should reference the specific experiment finding it draws from.

{{
  "title": "<experiment name + punchy descriptor>",
  "caption": "<LinkedIn caption — opens with sharp claim from the headline stat, adds context, under 150 words, ends with 'Comment BRAINAI and I\\'ll send it to you.'>",
  "slides": [
    {{"number": 1, "type": "cover",       "headline": "<MAX 8 WORDS — headline stat as scroll-stopper, promise not topic>", "body": "<max 40 words>", "visual_note": "<pure visual, no text in image>", "save_worthy": false, "trending_peg": "<stat source>"}},
    {{"number": 2, "type": "confirm",     "headline": "<max 10 words — open the problem, raise stakes>", "body": "<max 40 words — what this costs the field or practitioners>", "visual_note": "<pure visual, no text in image>", "save_worthy": false, "trending_peg": null}},
    {{"number": 3, "type": "build",       "headline": "<max 10 words — key finding 1, standalone>", "body": "<max 40 words — works cold with zero context>", "visual_note": "<pure visual, no text in image>", "save_worthy": false, "trending_peg": "<finding>"}},
    {{"number": 4, "type": "build",       "headline": "<max 10 words — key finding 2, standalone>", "body": "<max 40 words>", "visual_note": "<pure visual, no text in image>", "save_worthy": false, "trending_peg": "<finding>"}},
    {{"number": 5, "type": "save_worthy", "headline": "<max 10 words — a framework, stat or line sharp enough to quote>", "body": "<max 40 words — the slide people screenshot and send to a colleague>", "visual_note": "<pure visual, no text in image>", "save_worthy": true, "trending_peg": null}},
    {{"number": 6, "type": "climax",      "headline": "<max 10 words — Amphora's specific answer>", "body": "<max 40 words — TRIBE v2, Broca's area, fMRI. Concrete payoff.>", "visual_note": "<pure visual brain scan imagery, no text in image>", "save_worthy": false, "trending_peg": null}},
    {{"number": 7, "type": "cta",         "headline": "<max 8 words — one action + one reward>", "body": "<max 2 sentences — comment trigger>", "visual_note": "<pure visual, no text in image>", "save_worthy": false, "trending_peg": null}}
  ],
  "hashtags": ["#BrainAI", "#fMRI", "#NLP", "#GenerativeAI", "#Neuroscience"]
}}
""".strip()

    raw_json = run_agent(SYSTEM_PROMPT, user_message, max_tokens=4096)
    return _parse_json(raw_json)


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

_SLIDE_COLORS = {
    "cover":       ("#0f0f0f", "#f5f5f5"),
    "confirm":     ("#1a0a0a", "#ffdddd"),
    "build":       ("#1a1a2e", "#e8e8ff"),
    "save_worthy": ("#0d2b0d", "#a8ffb0"),   # green — signals save this
    "climax":      ("#0a2540", "#00d4ff"),
    "cta":         ("#1a1a1a", "#ffffff"),
    # legacy keys kept for backward compat
    "hook":        ("#0f0f0f", "#f5f5f5"),
    "trend":       ("#1a1a2e", "#e8e8ff"),
    "synthesis":   ("#0d1117", "#c9d1d9"),
    "amphora":     ("#0a2540", "#00d4ff"),
    "finding":     ("#1a1a2e", "#e8e8ff"),
}

_SLIDE_LABELS = {
    "cover":       "",
    "confirm":     "THE PROBLEM",
    "build":       "TRENDING",
    "save_worthy": "★ SAVE THIS",
    "climax":      "AMPHORA",
    "cta":         "",
    "hook":        "",
    "trend":       "TRENDING",
    "synthesis":   "THE PATTERN",
    "amphora":     "AMPHORA",
    "finding":     "FINDING",
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

        is_save   = slide.get("save_worthy", False)
        label_html = f'<div class="label">{label}</div>' if label else ""
        save_html  = '<div class="save-badge">★ SAVE THIS SLIDE</div>' if is_save else ""
        peg_html   = f'<div class="peg">⚡ {peg}</div>' if peg else ""
        num_html   = f'<div class="num">{num} / {n_slides}</div>'

        img_uri = images.get(num, "")
        if img_uri:
            bg_style = f"background-image: url('{img_uri}'); background-size: cover; background-position: center;"
            overlay  = '<div class="img-overlay"></div>'
        else:
            bg_style = f"background: {bg};"
            overlay  = ""

        slides_html += f"""
<div class="slide{'  save-worthy-slide' if is_save else ''}" style="{bg_style} color:{fg};">
  {overlay}
  <div class="content">
    {num_html}
    {label_html}
    {save_html}
    <div class="headline">{headline}</div>
    <div class="body-text">{body}</div>
    {peg_html}
  </div>
</div>
"""

    hashtags = " ".join(slideshow.get("hashtags", []))
    caption  = slideshow.get("caption", "")
    title    = slideshow.get("title", "Amphora Trend Carousel")

    caption_html = f"""
<div class="caption-block">
  <div class="caption-label">LINKEDIN CAPTION (Rule 06 — the second post)</div>
  <div class="caption-text">{caption}</div>
  <div class="caption-tags">{hashtags}</div>
</div>""" if caption else f'<div class="hashtags">{hashtags}</div>'

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
  .save-worthy-slide {{ outline: 3px solid #a8ffb0; outline-offset: 3px; }}
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
            opacity: .7; margin-top: 4px; color: #fff; text-transform: uppercase; }}
  .save-badge {{ font-size: 10px; font-weight: 800; letter-spacing: .2em;
                 color: #a8ffb0; margin-top: 4px; }}
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
  .caption-block {{
    width: 600px; margin: 40px auto 0;
    background: #1a1a1a; border: 1px solid #333;
    border-radius: 12px; padding: 28px;
  }}
  .caption-label {{ font-size: 10px; font-weight: 700; letter-spacing: .2em;
                    color: #555; text-transform: uppercase; margin-bottom: 16px; }}
  .caption-text {{ font-size: 14px; line-height: 1.7; color: #ccc;
                   white-space: pre-wrap; }}
  .caption-tags {{ font-size: 12px; color: #555; margin-top: 16px; line-height: 1.8; }}
  @media print {{
    body {{ background: #000; padding: 0; }}
    .slide {{ margin: 0; border-radius: 0; width: 100vw; height: 100vh; }}
    .caption-block {{ display: none; }}
  }}
</style>
</head>
<body>
<h1>{title}</h1>
{slides_html}
{caption_html}
</body>
</html>"""
