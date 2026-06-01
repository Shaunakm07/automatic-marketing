"""
Daily slideshow pipeline — generates a LinkedIn carousel from today's trend report.

Runs after daily_trends (trend report must already exist in Supabase).
Saves the rendered HTML as a 'slideshow' draft for review in the dashboard.
"""

import argparse
import logging
from rich.console import Console
from rich.panel   import Panel

from integrations import supabase_store, image_gen
from agents       import slideshow_agent
from config.settings import DRY_RUN

log     = logging.getLogger(__name__)
console = Console()


def run(dry_run: bool = False) -> dict:
    import os
    if dry_run:
        os.environ["DRY_RUN"] = "true"

    console.print(Panel("[bold]Amphora Slideshow Pipeline[/bold]", style="magenta"))
    console.print(f"DRY_RUN={DRY_RUN or dry_run}\n")

    # 1. Fetch latest trend report
    console.print("  [1/3] Fetching latest trend report...")
    row = supabase_store.get_latest_trend_report()
    if not row:
        console.print("  [red]No trend report found — run the trend pipeline first.[/red]")
        raise RuntimeError("No trend report available")

    report = row["report"]
    console.print(f"      Report from: {row['created_at'][:19]}")
    console.print(f"      Sources: {', '.join(row.get('sources_used', []))}")

    # 2. Generate slides
    console.print("  [2/3] Generating slides with Claude...")
    slideshow = slideshow_agent.generate_slides(report)
    title     = slideshow.get("title", "Amphora Trend Carousel")
    n_slides  = len(slideshow.get("slides", []))
    console.print(f"      Title: [green]{title}[/green]")
    console.print(f"      Slides: {n_slides}")
    for s in slideshow.get("slides", []):
        console.print(f"      [{s['number']}] {s['type'].upper()}: {s['headline'][:60]}")

    # 3. Generate background images
    console.print("  [3/4] Generating slide background images...")
    import os
    if os.environ.get("HF_TOKEN"):
        images = image_gen.generate_all(slideshow.get("slides", []))
        console.print(f"      Generated {len(images)}/{n_slides} images")
    else:
        images = {}
        console.print("      [dim]HF_TOKEN not set — skipping image generation[/dim]")

    # 4. Render and save
    console.print("  [4/4] Saving slideshow draft...")
    html = slideshow_agent.render_html(slideshow, images=images)
    if not (DRY_RUN or dry_run):
        import json
        draft_id = supabase_store.save_draft(
            content_type = "slideshow",
            title        = title,
            body         = html,
            metadata     = {
                "slides":        slideshow.get("slides", []),
                "hashtags":      slideshow.get("hashtags", []),
                "trend_report":  row["id"],
                "sources_used":  row.get("sources_used", []),
            },
        )
        console.print(f"      Saved draft ID: [green]{draft_id}[/green]")
    else:
        console.print("      [dim]DRY RUN — not saving to Supabase[/dim]")

    console.print(Panel("[bold green]Slideshow generation complete[/bold green]", style="green"))
    return slideshow


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
