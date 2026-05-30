"""
Content strategy — defines Amphora's voice, pillars, and rotation rules.
All agents read from this file so the brand stays consistent.
"""

BRAND_VOICE = """
Amphora's voice is:
- Direct and confident — we know this works, we have the data
- Technically credible but not exclusionary — explain the mechanism, skip the jargon wall
- Genuinely excited about the science — this IS exciting, let that show
- Human-centric — the ultimate goal is AI that understands feeling

Never: hypey buzzword salads, vague "AI will change everything" claims,
       or academic abstraction that loses a non-neuroscientist reader
"""

COMPANY_DESCRIPTION = """
Amphora gives generative AI a biological basis for feeling.
Our fMRI prediction engine (TRIBE v2) maps any text or visual input to
predicted brain activation patterns. We fine-tune language models to
maximise or minimise specific neural responses — starting with Broca's
area, the brain's language centre — producing AI outputs that are
measurably more engaging, coherent, and emotionally resonant.
"""

CONTENT_PILLARS = [
    {
        "id": "research_insight",
        "name": "Research Insight",
        "description": "A specific, concrete finding from the latest experiment. Lead with the number or result, then explain what it means.",
        "tone": "precise, evidence-forward",
        "example_hook": "We trained a language model to maximise Broca's area activation. At step 200, it was producing text that a blind judge rated as higher quality on every axis — engagement, clarity, coherence, creativity, instruction following.",
    },
    {
        "id": "behind_the_scenes",
        "name": "Behind the Science",
        "description": "How the technology works. Pick one interesting mechanism and explain it clearly for a technical-but-not-neuroscience audience.",
        "tone": "educational, curious, shows depth",
        "example_hook": "How do you teach an AI what 'engaging' means without using human ratings? You use fMRI data from 8,000 hours of natural human reading.",
    },
    {
        "id": "vision",
        "name": "Vision & Narrative",
        "description": "Why this matters for the future of AI. Connect the specific work to the broader mission. Accessible to anyone.",
        "tone": "inspiring, grounded in specifics, no vague promises",
        "example_hook": "Every LLM trained today knows what grammatically correct looks like. None of them know what it feels like in a human brain to read something beautiful. We're changing that.",
    },
]

PILLAR_ROTATION = ["research_insight", "behind_the_scenes", "vision"]

HASHTAGS = {
    "research_insight":   ["#BrainAI", "#fMRI", "#NLP", "#GenerativeAI", "#Neuroscience"],
    "behind_the_scenes":  ["#MachineLearning", "#AIResearch", "#RLHF", "#LoRA", "#LLM"],
    "vision":             ["#EmotionalAI", "#FutureOfAI", "#ArtificialIntelligence", "#AmphoraAI"],
}

LINKEDIN_POST_CONSTRAINTS = {
    "max_chars": 2800,
    "ideal_chars": 1200,
    "line_break_after_hook": True,
    "no_markdown_bold": True,
    "emoji_allowed": False,
    "end_with_question": True,
}

VIDEO_STYLE = {
    "duration_seconds": 60,
    "style": "cinematic scientific documentary",
    "narration": "first person plural (we), present tense",
    "visual_focus": "brain scans, text on screen, clean data visualisations",
}
