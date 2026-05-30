"""
Standalone regeneration script — called by the regenerate_draft GitHub Actions workflow.

Reads REGEN_ITEM_ID and REGEN_INSTRUCTIONS from environment (set by the workflow
so special characters in instructions are handled safely).
"""

import json
import os
import sys

sys.path.insert(0, ".")


def main() -> None:
    item_id      = os.environ["REGEN_ITEM_ID"]
    instructions = os.environ.get("REGEN_INSTRUCTIONS", "")

    from integrations import supabase_store
    from agents import blog_agent

    items = supabase_store.get_drafts()
    draft = next((i for i in items if i["id"] == item_id), None)
    if not draft:
        print(f"Draft {item_id} not found", file=sys.stderr)
        sys.exit(1)

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
        print("Cannot regenerate — no matching digest found", file=sys.stderr)
        sys.exit(1)

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

    extra     = f"\nAdditional instructions: {instructions}" if instructions else ""
    new_body  = blog_agent.write_blog_post(digest, extra_context=extra)
    new_title = blog_agent.write_blog_title(digest)

    supabase_store.delete_draft(item_id)
    supabase_store.save_draft(
        content_type=draft["content_type"],
        title=new_title,
        body=new_body,
        metadata={**metadata, "regenerated": True},
    )
    print(f"Done: {new_title}")


if __name__ == "__main__":
    main()
