"""
Daily trends pipeline — fetches what's trending and generates viral content angles.

Triggered daily at 7 AM PT (before the LinkedIn post goes out at 9 AM),
so the LinkedIn agent can optionally pull the freshest viral angle.
"""

import argparse
import logging
from rich.console import Console
from rich.panel   import Panel

from integrations import trend_scraper, supabase_store
from agents       import trend_agent
from config.settings import DRY_RUN

log     = logging.getLogger(__name__)
console = Console()


def run(dry_run: bool = False) -> dict:
    import os
    if dry_run:
        os.environ["DRY_RUN"] = "true"

    console.print(Panel("[bold]Amphora Trend Analysis Pipeline[/bold]", style="cyan"))
    console.print(f"DRY_RUN={DRY_RUN or dry_run}\n")

    # 1. Scrape
    console.print("  [1/3] Scraping trending content...")
    raw = trend_scraper.fetch_all()
    console.print(f"      Sources: {', '.join(raw['sources_used'])}")
    console.print(
        f"      Items: {len(raw['hn'])} HN | "
        f"{len(raw['reddit'])} Reddit | "
        f"{len(raw['arxiv'])} ArXiv | "
        f"{len(raw['hf'])} HF | "
        f"{len(raw['biorxiv'])} BioRxiv | "
        f"{len(raw['bluesky'])} Bluesky | "
        f"{len(raw['lobsters'])} Lobsters | "
        f"{len(raw['twitter'])} X"
    )

    # 2. Analyse
    console.print("  [2/3] Analysing with Claude...")
    report = trend_agent.analyse_trends(raw)
    console.print(f"      Summary: {report['summary'][:120]}…")
    console.print(f"      Top viral angle (score {report['viral_angles'][0]['virality_score']}): "
                  f"{report['viral_angles'][0]['hook'][:100]}…")

    # 3. Save
    console.print("  [3/3] Saving trend report...")
    if not (DRY_RUN or dry_run):
        report_id = supabase_store.save_trend_report(
            report       = report,
            sources_used = raw["sources_used"],
        )
        console.print(f"      Saved report ID: [green]{report_id}[/green]")
    else:
        console.print("      [dim]DRY RUN — not saving to Supabase[/dim]")

    console.print(Panel("[bold green]Trend analysis complete[/bold green]", style="green"))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
