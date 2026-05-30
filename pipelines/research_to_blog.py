"""
Research-to-blog pipeline.

Triggered by: push to Brain-LLM-Fine-Tuning (via GitHub Actions webhook)
              or manually: python -m pipelines.research_to_blog

Runs the full orchestrator pipeline for any unprocessed experiments.
"""

import argparse
import json
from rich.console import Console
from agents.orchestrator import run_full_pipeline

console = Console()


def run(force_reprocess: bool = False, dry_run: bool = False) -> None:
    import os
    if dry_run:
        os.environ["DRY_RUN"] = "true"

    results = run_full_pipeline(force_reprocess=force_reprocess)

    if not results:
        console.print("[dim]No new experiments to process.[/dim]")
        return

    console.print(f"\n[bold green]Processed {len(results)} experiment(s):[/bold green]")
    for r in results:
        console.print(f"\n  {r['experiment_name']}")
        console.print(f"    Headline:       {r['headline_stat']}")
        console.print(f"    Blog title:     {r['blog_title']}")
        console.print(f"    LinkedIn queue: {len(r['linkedin_queue'])} posts added")
        console.print(f"    Video job ID:   {r['video_job_id']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force",   action="store_true", help="Reprocess even if already digested")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()
    run(force_reprocess=args.force, dry_run=args.dry_run)
