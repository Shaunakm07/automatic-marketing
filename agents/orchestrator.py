"""
OrchestratorAgent — coordinates the full marketing pipeline.

Reads new experiment files → digests them → generates blog + slideshow
+ video script → saves everything to Supabase as drafts.
Nothing is published until explicitly approved via the dashboard.
"""

import logging
from rich.console import Console
from rich.panel   import Panel

from agents        import research_agent, blog_agent, slideshow_agent, video_agent
from integrations  import github_reader, supabase_store, image_gen
from config.settings import DRY_RUN

log     = logging.getLogger(__name__)
console = Console()


def process_new_experiment(experiment_name: str, experiment_md: str) -> dict:
    """
    Full pipeline for a single experiment file.

    Steps:
      1. ResearchAgent    → structured digest
      2. BlogAgent        → blog post (saved as draft)
      3. SlideshowAgent   → 7-slide carousel from research findings (saved as draft)
      4. VideoAgent       → video script + Higgsfield job (saved as draft)
    """
    console.print(Panel(f"Processing: [bold]{experiment_name}[/bold]", style="cyan"))

    # 1. Research digest
    console.print("  [1/4] Digesting experiment...")
    digest = research_agent.digest_experiment(experiment_name, experiment_md)
    digest_id = supabase_store.save_research_digest(
        experiment_name = experiment_name,
        summary         = digest["narrative"],
        key_findings    = digest["key_findings"],
    ) if not DRY_RUN else "dry-run-digest-id"
    console.print(f"      Headline: [green]{digest['headline_stat']}[/green]")

    # 2. Blog post
    console.print("  [2/4] Writing blog post...")
    blog_md    = blog_agent.write_blog_post(digest)
    blog_title = blog_agent.write_blog_title(digest)
    blog_id = supabase_store.save_draft(
        content_type = "blog",
        title        = blog_title,
        body         = blog_md,
        metadata     = {"experiment": experiment_name, "digest_id": digest_id},
    ) if not DRY_RUN else "dry-run-blog-id"
    console.print(f"      Title: [green]{blog_title}[/green]")

    # 3. Slideshow carousel
    console.print("  [3/4] Generating research slideshow...")
    show     = slideshow_agent.generate_slides_from_digest(digest)
    console.print(f"      Carousel: [green]{show['title']}[/green]")
    console.print("      Generating slide backgrounds...")
    images   = image_gen.generate_all(show.get("slides", [])) if not DRY_RUN else {}
    console.print(f"      Images: {len(images)}/{len(show.get('slides', []))}")
    html     = slideshow_agent.render_html(show, images=images)
    show_id  = supabase_store.save_draft(
        content_type = "slideshow",
        title        = show["title"],
        body         = html,
        metadata     = {
            "slides":      show.get("slides", []),
            "hashtags":    show.get("hashtags", []),
            "experiment":  experiment_name,
            "digest_id":   digest_id,
            "source":      "research",
        },
    ) if not DRY_RUN else "dry-run-show-id"

    # 4. Video
    console.print("  [4/4] Generating video script + Higgsfield job...")
    video_result = video_agent.generate_video(digest, blog_excerpt=blog_md[:600])
    video_id = supabase_store.save_draft(
        content_type = "video_script",
        title        = f"Video: {experiment_name}",
        body         = video_result["script"],
        metadata     = {
            "higgsfield_prompt": video_result["higgsfield_prompt"],
            "job_id":            video_result["job_id"],
            "experiment":        experiment_name,
        },
    ) if not DRY_RUN else "dry-run-video-id"
    console.print(f"      Higgsfield job: [green]{video_result['job_id']}[/green]")

    summary = {
        "experiment_name": experiment_name,
        "headline_stat":   digest["headline_stat"],
        "blog_id":         blog_id,
        "blog_title":      blog_title,
        "slideshow_id":    show_id,
        "slideshow_title": show["title"],
        "video_job_id":    video_result["job_id"],
        "video_id":        video_id,
    }
    console.print(Panel("[bold green]Pipeline complete[/bold green]", style="green"))
    return summary


def run_full_pipeline(force_reprocess: bool = False) -> list[dict]:
    """
    Fetch all EXPERIMENT*.md files from Brain-LLM-Fine-Tuning and process
    any that haven't been digested yet.
    """
    console.print("[bold]Amphora Marketing Orchestrator[/bold]")
    console.print(f"DRY_RUN={DRY_RUN}\n")

    experiments = github_reader.fetch_all_experiments()
    console.print(f"Found {len(experiments)} experiment files.\n")

    results = []
    for name, content in experiments:
        existing = supabase_store.get_research_digest(name) if not DRY_RUN else None
        if existing and not force_reprocess:
            console.print(f"  [dim]Skipping {name} — already digested[/dim]")
            continue
        result = process_new_experiment(name, content)
        results.append(result)

    return results
