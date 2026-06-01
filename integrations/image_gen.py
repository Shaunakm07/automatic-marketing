"""
Image generation for slideshow backgrounds.

Uses HuggingFace Inference API (fal-ai provider) with Qwen/Qwen-Image.
All images are generated in the same punk zine / risograph print style
so the carousel has a cohesive visual identity.

Requires HF_TOKEN in environment.
"""

import base64
import io
import os

# Fixed style applied to every slide — describes the visual treatment.
# The slide's visual_note provides the subject matter; this wraps it.
_STYLE_SUFFIX = (
    ". Style: aggressive color misregistration — a clashing combination of vibrant fluorescent "
    "neon and deep saturated colors with large intentional offsets bleeding onto a dark, contrasting "
    "background. Coarse uneven halftone dot patterns on all surfaces. Rough torn-paper edges on "
    "all forms. Unrefined ink bleed along edges. Heavily distressed texture — crumpled coarse-fiber "
    "paper with ink speckles and visible paper fibers. Flat solid color fields over dot textures, "
    "no gradients. Unnatural palette selected for maximum jarring contrast. Punk zine aesthetic. "
    "ABSOLUTELY NO TEXT, NO WORDS, NO LETTERS, NO NUMBERS, NO TYPOGRAPHY, NO WRITING OF ANY KIND "
    "anywhere in the image. Pure visual only."
)


def generate_background(visual_note: str) -> str:
    """
    Generate a slide background image from a visual note.

    Returns a base64 PNG data URI ready for use as CSS background-image.
    Returns empty string on failure so the caller falls back to solid color.
    """
    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        return ""

    try:
        from huggingface_hub import InferenceClient

        # FLUX.1-schnell runs on HuggingFace's own inference (free within rate limits).
        # No provider= needed — HF hosts this model directly.
        client = InferenceClient(api_key=hf_token)
        prompt = visual_note.rstrip(".") + _STYLE_SUFFIX
        image  = client.text_to_image(prompt, model="black-forest-labs/FLUX.1-schnell")

        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"

    except Exception as e:
        print(f"[image_gen] Failed for '{visual_note[:60]}…': {e}")
        return ""


def generate_all(slides: list[dict]) -> dict[int, str]:
    """
    Generate background images for all slides.
    Returns {slide_number: data_uri} — missing entries mean use solid color fallback.
    """
    images: dict[int, str] = {}
    for slide in slides:
        num  = slide.get("number", 0)
        note = slide.get("visual_note", "")
        if note:
            print(f"  [image_gen] Slide {num}: {note[:60]}…")
            uri = generate_background(note)
            if uri:
                images[num] = uri
    return images
