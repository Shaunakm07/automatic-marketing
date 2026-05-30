"""
Content store backed by Supabase.

Tables (create with the SQL in migrations/001_create_tables.sql):
  content_items   — all generated drafts and published pieces
  content_queue   — scheduled LinkedIn posts
  research_digests — processed experiment summaries
"""

import json
from datetime import datetime, timezone
from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY


def _client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# ---------------------------------------------------------------------------
# Content items
# ---------------------------------------------------------------------------

def save_draft(
    content_type: str,     # "blog", "linkedin", "video_script", "research_digest"
    title:        str,
    body:         str,
    metadata:     dict | None = None,
) -> str:
    """Insert a draft and return its ID."""
    row = {
        "content_type": content_type,
        "title":        title,
        "body":         body,
        "status":       "draft",
        "metadata":     json.dumps(metadata or {}),
        "created_at":   datetime.now(timezone.utc).isoformat(),
    }
    result = _client().table("content_items").insert(row).execute()
    return result.data[0]["id"]


def get_drafts(content_type: str | None = None) -> list[dict]:
    q = _client().table("content_items").select("*").eq("status", "draft")
    if content_type:
        q = q.eq("content_type", content_type)
    return q.order("created_at", desc=True).execute().data


def mark_published(item_id: str, published_url: str | None = None) -> None:
    update = {"status": "published", "published_at": datetime.now(timezone.utc).isoformat()}
    if published_url:
        update["published_url"] = published_url
    _client().table("content_items").update(update).eq("id", item_id).execute()


# ---------------------------------------------------------------------------
# LinkedIn queue
# ---------------------------------------------------------------------------

def enqueue_linkedin_post(post_text: str, pillar: str, source_id: str | None = None) -> str:
    row = {
        "post_text":   post_text,
        "pillar":      pillar,
        "status":      "queued",
        "source_id":   source_id,
        "created_at":  datetime.now(timezone.utc).isoformat(),
        "scheduled_for": None,
    }
    result = _client().table("content_queue").insert(row).execute()
    return result.data[0]["id"]


def get_next_queued_post() -> dict | None:
    result = (
        _client()
        .table("content_queue")
        .select("*")
        .eq("status", "queued")
        .order("created_at")
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def mark_post_sent(queue_id: str, linkedin_post_id: str) -> None:
    _client().table("content_queue").update({
        "status":        "sent",
        "sent_at":       datetime.now(timezone.utc).isoformat(),
        "linkedin_id":   linkedin_post_id,
    }).eq("id", queue_id).execute()


def get_recent_pillars(n: int = 7) -> list[str]:
    """Return the pillar of the last n sent posts (for rotation logic)."""
    result = (
        _client()
        .table("content_queue")
        .select("pillar")
        .eq("status", "sent")
        .order("sent_at", desc=True)
        .limit(n)
        .execute()
    )
    return [r["pillar"] for r in result.data]


# ---------------------------------------------------------------------------
# Research digests
# ---------------------------------------------------------------------------

def save_research_digest(experiment_name: str, summary: str, key_findings: list[str]) -> str:
    row = {
        "experiment_name": experiment_name,
        "summary":         summary,
        "key_findings":    json.dumps(key_findings),
        "created_at":      datetime.now(timezone.utc).isoformat(),
    }
    result = _client().table("research_digests").insert(row).execute()
    return result.data[0]["id"]


def get_research_digest(experiment_name: str) -> dict | None:
    result = (
        _client()
        .table("research_digests")
        .select("*")
        .eq("experiment_name", experiment_name)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def list_research_digests() -> list[dict]:
    return (
        _client()
        .table("research_digests")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
    )
