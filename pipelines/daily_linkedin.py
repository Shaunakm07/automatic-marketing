"""
Daily LinkedIn pipeline — runs every day at 9 AM PT via GitHub Actions.

Fetches the next queued post from Supabase and publishes it to LinkedIn.
If the queue is empty, generates a fresh post from the latest research digest.
"""

import argparse
import logging
from rich.console import Console

from integrations  import supabase_store, linkedin
from agents        import linkedin_agent, research_agent
from integrations  import github_reader
from config.settings import DRY_RUN

log     = logging.getLogger(__name__)
console = Console()


def run(dry_run: bool = False) -> None:
    import os
    if dry_run:
        os.environ["DRY_RUN"] = "true"

    console.print("[bold]Daily LinkedIn Pipeline[/bold]")

    # 1. Get next queued post
    queued = supabase_store.get_next_queued_post()

    if queued is None:
        console.print("Queue empty — generating a fresh post from latest research...")
        exp_name, exp_md = github_reader.fetch_latest_experiment()
        digest = research_agent.digest_experiment(exp_name, exp_md)
        recent_pillars = supabase_store.get_recent_pillars(7)
        posts = linkedin_agent.generate_post_queue(digest, recent_pillars=recent_pillars, n_posts=1)
        post_text = posts[0]["text"]
        pillar    = posts[0]["pillar"]
        queue_id = supabase_store.enqueue_linkedin_post(post_text, pillar)
        queued   = {"id": queue_id, "post_text": post_text, "pillar": pillar}
        console.print(f"  Generated [{pillar}]: {post_text[:100]}…")

    post_text = queued["post_text"]
    queue_id  = queued["id"]

    console.print(f"\nPublishing [{queued['pillar']}] post ({len(post_text)} chars)...")

    linkedin_id = linkedin.post_text_update(post_text)
    supabase_store.mark_post_sent(queue_id, linkedin_id)

    console.print(f"[green]Published. LinkedIn ID: {linkedin_id}[/green]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
