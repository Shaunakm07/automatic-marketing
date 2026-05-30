"""LinkedIn API wrapper — post text updates to Amphora's LinkedIn profile."""

import httpx
from config.settings import LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN, LINKEDIN_API_BASE, DRY_RUN


def post_text_update(text: str) -> str:
    """
    Publish a text post on LinkedIn. Returns the post URN.
    In dry-run mode prints the post and returns a fake URN.
    """
    if DRY_RUN:
        print(f"\n[DRY RUN] LinkedIn post would be:\n{'─'*60}\n{text}\n{'─'*60}\n")
        return "urn:li:share:DRY_RUN_0000000000"

    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type":  "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author":     LINKEDIN_PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }
    r = httpx.post(
        f"{LINKEDIN_API_BASE}/ugcPosts",
        headers=headers,
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.headers.get("x-restli-id", "unknown")
