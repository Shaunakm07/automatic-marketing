"""
Weekly video pipeline — runs every Monday via GitHub Actions.

Generates a Higgsfield video from the latest research digest + latest blog post.
Polls for completion and saves the video URL to Supabase.
"""

import argparse
from rich.console import Console

from agents        import video_agent, research_agent
from integrations  import github_reader, supabase_store, higgsfield
from config.settings import DRY_RUN

console = Console()


def run(dry_run: bool = False, wait: bool = False) -> None:
    import os
    if dry_run:
        os.environ["DRY_RUN"] = "true"

    console.print("[bold]Weekly Video Pipeline[/bold]")

    # Get latest experiment + digest
    exp_name, exp_md = github_reader.fetch_latest_experiment()
    console.print(f"  Latest experiment: {exp_name}")

    digest = research_agent.digest_experiment(exp_name, exp_md)

    # Get the latest published/draft blog post for tone reference
    blog_drafts  = supabase_store.get_drafts("blog")
    blog_excerpt = blog_drafts[0]["body"][:800] if blog_drafts else ""

    console.print("  Generating video script + submitting Higgsfield job...")
    result = video_agent.generate_video(digest, blog_excerpt=blog_excerpt)

    video_id = supabase_store.save_draft(
        content_type = "video_script",
        title        = f"Weekly video: {exp_name}",
        body         = result["script"],
        metadata     = {
            "higgsfield_prompt": result["higgsfield_prompt"],
            "job_id":            result["job_id"],
            "experiment":        exp_name,
        },
    )

    console.print(f"  [green]Higgsfield job ID: {result['job_id']}[/green]")
    console.print(f"  Script saved as draft ID: {video_id}")

    if wait and not DRY_RUN:
        console.print("\n  Waiting for Higgsfield to complete (up to 30 min)...")
        video_url = higgsfield.wait_for_completion(result["job_id"])
        supabase_store.mark_published(video_id, published_url=video_url)
        console.print(f"  [green]Video ready: {video_url}[/green]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--wait",    action="store_true",
                        help="Poll Higgsfield until job completes and save video URL")
    args = parser.parse_args()
    run(dry_run=args.dry_run, wait=args.wait)
