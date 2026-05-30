"""
Amphora Marketing Ops — FastAPI backend.

Serves the dashboard at / and exposes the pipeline, content, and trend APIs at /api/*.

Run:
    uvicorn api.main:app --reload --port 8000
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

log = logging.getLogger(__name__)

app = FastAPI(title="Amphora Marketing Ops", version="1.0.0")

# On Vercel, background tasks are killed immediately after the HTTP response,
# so pipeline triggers dispatch GitHub Actions workflow_dispatch events instead.
_ON_VERCEL = bool(os.getenv("VERCEL"))
_MARKETING_REPO = os.getenv("MARKETING_REPO", "Shaunakm07/automatic-marketing")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DASHBOARD_PATH = Path(__file__).parent.parent / "dashboard" / "index.html"


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def serve_dashboard():
    return FileResponse(DASHBOARD_PATH)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@app.get("/api/stats")
async def get_stats():
    from integrations import supabase_store
    try:
        drafts       = supabase_store.get_drafts()
        queue        = supabase_store.list_queued_posts()
        trend        = supabase_store.get_latest_trend_report()
        digests      = supabase_store.list_research_digests()
        return {
            "drafts_pending": len(drafts),
            "queue_depth":    len(queue),
            "last_trend_at":  trend["created_at"] if trend else None,
            "total_digests":  len(digests),
        }
    except Exception as e:
        log.exception("stats error")
        raise HTTPException(500, str(e))


# ---------------------------------------------------------------------------
# Drafts
# ---------------------------------------------------------------------------

@app.get("/api/drafts")
async def list_drafts(type: str | None = None):
    from integrations import supabase_store
    try:
        return supabase_store.get_drafts(content_type=type)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/drafts/{item_id}")
async def get_draft(item_id: str):
    from integrations import supabase_store
    try:
        items = supabase_store.get_drafts()
        match = next((i for i in items if i["id"] == item_id), None)
        if not match:
            raise HTTPException(404, "Draft not found")
        return match
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/drafts/{item_id}/approve")
async def approve_draft(item_id: str):
    from integrations import supabase_store
    try:
        supabase_store.mark_published(item_id)
        return {"status": "published", "id": item_id}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/drafts/{item_id}/reject")
async def reject_draft(item_id: str):
    from integrations import supabase_store
    try:
        supabase_store.delete_draft(item_id)
        return {"status": "deleted", "id": item_id}
    except Exception as e:
        raise HTTPException(500, str(e))


class RegenerateRequest(BaseModel):
    instructions: str = ""


@app.post("/api/drafts/{item_id}/regenerate")
async def regenerate_draft(item_id: str, body: RegenerateRequest):
    from integrations import supabase_store

    items = supabase_store.get_drafts()
    draft = next((i for i in items if i["id"] == item_id), None)
    if not draft:
        raise HTTPException(404, "Draft not found")

    if _ON_VERCEL:
        return _dispatch_github_workflow(
            "regenerate_draft.yml",
            inputs={"item_id": item_id, "instructions": body.instructions},
        )

    def _regen():
        import json
        from agents import blog_agent

        metadata = draft.get("metadata") or {}
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                metadata = {}

        experiment_name = metadata.get("experiment", draft["title"])
        digest_id       = metadata.get("digest_id")

        digests    = supabase_store.list_research_digests()
        digest_row = next(
            (d for d in digests if d["id"] == digest_id or d["experiment_name"] == experiment_name),
            None,
        )
        if not digest_row:
            log.warning("Cannot regenerate — no matching digest found")
            return

        digest = {
            "experiment_name": digest_row["experiment_name"],
            "narrative":       digest_row["summary"],
            "key_findings":    json.loads(digest_row["key_findings"])
                               if isinstance(digest_row["key_findings"], str)
                               else digest_row["key_findings"],
            "headline_stat":   "",
            "one_liner":       digest_row["summary"][:100],
            "content_angles":  [],
        }

        extra     = f"\nAdditional instructions: {body.instructions}" if body.instructions else ""
        new_body  = blog_agent.write_blog_post(digest, extra_context=extra)
        new_title = blog_agent.write_blog_title(digest)

        supabase_store.delete_draft(item_id)
        supabase_store.save_draft(
            content_type=draft["content_type"],
            title=new_title,
            body=new_body,
            metadata={**metadata, "regenerated": True},
        )

    import threading
    threading.Thread(target=_regen, daemon=True).start()
    return {"status": "regenerating", "id": item_id}


# ---------------------------------------------------------------------------
# LinkedIn queue
# ---------------------------------------------------------------------------

@app.get("/api/queue")
async def list_queue():
    from integrations import supabase_store
    try:
        return supabase_store.list_queued_posts()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/queue/{queue_id}/approve")
async def post_now(queue_id: str):
    from integrations import supabase_store, linkedin
    try:
        post = supabase_store.get_queue_item(queue_id)
        if not post:
            raise HTTPException(404, "Queue item not found")
        linkedin_id = linkedin.post_text_update(post["post_text"])
        supabase_store.mark_post_sent(queue_id, linkedin_id)
        return {"status": "sent", "linkedin_id": linkedin_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/queue/{queue_id}/skip")
async def skip_post(queue_id: str):
    from integrations import supabase_store
    try:
        supabase_store.skip_queue_item(queue_id)
        return {"status": "skipped", "id": queue_id}
    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------------------------------
# Research digests
# ---------------------------------------------------------------------------

@app.get("/api/digests")
async def list_digests():
    from integrations import supabase_store
    try:
        return supabase_store.list_research_digests()
    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------------------------------
# Trend reports
# ---------------------------------------------------------------------------

@app.get("/api/trends")
async def get_trends():
    from integrations import supabase_store
    try:
        report = supabase_store.get_latest_trend_report()
        if not report:
            raise HTTPException(404, "No trend reports found — run the trend pipeline first")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/trends/history")
async def trends_history():
    from integrations import supabase_store
    try:
        return supabase_store.list_trend_reports(limit=20)
    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------------------------------
# Pipeline triggers
# ---------------------------------------------------------------------------

_pipeline_status: dict[str, dict] = {
    "run":      {"running": False, "last_started": None},
    "linkedin": {"running": False, "last_started": None},
    "trends":   {"running": False, "last_started": None},
}


def _set_running(name: str, flag: bool):
    _pipeline_status[name]["running"] = flag
    if flag:
        _pipeline_status[name]["last_started"] = datetime.now(timezone.utc).isoformat()


def _dispatch_github_workflow(workflow_file: str, inputs: dict | None = None) -> dict:
    """Trigger a GitHub Actions workflow_dispatch event (used when running on Vercel)."""
    import httpx as _httpx
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        raise HTTPException(500, "GITHUB_TOKEN not set — cannot trigger workflow")
    payload: dict = {"ref": "main"}
    if inputs:
        payload["inputs"] = inputs
    r = _httpx.post(
        f"https://api.github.com/repos/{_MARKETING_REPO}/actions/workflows/{workflow_file}/dispatches",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json=payload,
        timeout=15,
    )
    if r.status_code == 204:
        return {"status": "triggered", "mode": "github_actions", "workflow": workflow_file}
    raise HTTPException(r.status_code, f"GitHub API: {r.text}")


@app.get("/api/pipeline/status")
async def pipeline_status():
    return {**_pipeline_status, "mode": "github_actions" if _ON_VERCEL else "local"}


@app.post("/api/pipeline/run")
async def run_full_pipeline(background_tasks: BackgroundTasks):
    if _ON_VERCEL:
        return _dispatch_github_workflow("research_to_blog.yml")

    if _pipeline_status["run"]["running"]:
        raise HTTPException(409, "Full pipeline already running")

    def _run():
        _set_running("run", True)
        try:
            from agents import orchestrator
            orchestrator.run_full_pipeline()
        finally:
            _set_running("run", False)

    background_tasks.add_task(_run)
    return {"status": "started", "pipeline": "run"}


@app.post("/api/pipeline/linkedin")
async def run_linkedin_pipeline(background_tasks: BackgroundTasks):
    if _ON_VERCEL:
        return _dispatch_github_workflow("daily_linkedin.yml")

    if _pipeline_status["linkedin"]["running"]:
        raise HTTPException(409, "LinkedIn pipeline already running")

    def _run():
        _set_running("linkedin", True)
        try:
            from pipelines import daily_linkedin
            daily_linkedin.run()
        finally:
            _set_running("linkedin", False)

    background_tasks.add_task(_run)
    return {"status": "started", "pipeline": "linkedin"}


@app.post("/api/pipeline/trends")
async def run_trends_pipeline(background_tasks: BackgroundTasks):
    if _ON_VERCEL:
        return _dispatch_github_workflow("daily_trends.yml")

    if _pipeline_status["trends"]["running"]:
        raise HTTPException(409, "Trend pipeline already running")

    def _run():
        _set_running("trends", True)
        try:
            from pipelines import daily_trends
            daily_trends.run()
        finally:
            _set_running("trends", False)

    background_tasks.add_task(_run)
    return {"status": "started", "pipeline": "trends"}
