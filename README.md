# Automatic Marketing — Amphora

An autonomous agent pipeline that handles all marketing for Amphora. Zero manual effort: the system reads experiment results, writes blogs, generates LinkedIn posts, and produces Higgsfield videos — on schedule, every day.

---

## What It Does

| Output | Trigger | Agent |
|--------|---------|-------|
| LinkedIn post | Daily cron (9 AM PT) | `LinkedInAgent` |
| Blog post | New experiment results pushed to Brain-LLM-Fine-Tuning | `BlogAgent` |
| Higgsfield video script | Weekly or on blog publish | `VideoAgent` |
| Research digest | New EXPERIMENT*.md detected | `ResearchAgent` |
| Content calendar | Weekly | `OrchestratorAgent` |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Orchestrator                    │
│  Reads experiment results → decides what to make │
└─────────┬───────────┬───────────┬───────────────┘
          │           │           │
    ResearchAgent  BlogAgent  LinkedInAgent   VideoAgent
          │           │           │               │
    GitHub API   Supabase    LinkedIn API   Higgsfield API
    (pull .md)   (publish)   (post)         (generate)
```

All agents are powered by `claude-sonnet-4-6` via the Anthropic API. Each agent has a dedicated system prompt in `prompts/`.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Fill in keys — see .env.example for all required variables
```

### 3. Test the pipeline end-to-end (dry run)

```bash
python -m pipelines.daily_linkedin --dry_run
python -m pipelines.research_to_blog --dry_run
```

### 4. Deploy to GitHub Actions

Push to `main`. The workflows in `.github/workflows/` activate automatically.

---

## Key Files

| Path | Purpose |
|------|---------|
| `agents/orchestrator.py` | Coordinates the full pipeline |
| `agents/research_agent.py` | Reads experiment .md files, extracts insights |
| `agents/blog_agent.py` | Writes technical blog posts from research |
| `agents/linkedin_agent.py` | Writes and posts daily LinkedIn content |
| `agents/video_agent.py` | Generates Higgsfield video scripts + submits jobs |
| `integrations/higgsfield.py` | Higgsfield AI API wrapper |
| `integrations/linkedin.py` | LinkedIn API wrapper |
| `integrations/github_reader.py` | Fetches experiment results from Brain-LLM repo |
| `integrations/supabase_store.py` | Content store — drafts, published, history |
| `pipelines/daily_linkedin.py` | Entrypoint for daily LinkedIn post pipeline |
| `pipelines/research_to_blog.py` | Entrypoint for experiment → blog pipeline |
| `pipelines/weekly_video.py` | Entrypoint for weekly Higgsfield video pipeline |
| `prompts/` | System + user prompt templates for each agent |

---

## Content Strategy

The system has a defined content strategy baked into `config/strategy.py`. LinkedIn posts rotate through three content pillars:

1. **Research insight** — a finding from the latest experiment, made accessible
2. **Behind the scenes** — how the technology works, for a technical audience
3. **Vision + narrative** — why this matters, for a broader audience

The orchestrator ensures the last 7 days don't repeat the same pillar twice in a row.

---

## Adding a New Experiment

When you push a new `EXPERIMENT*.md` to `https://github.com/Shaunakm07/Brain-LLM-Fine-Tuning`:

1. The `research_digest` GitHub Action triggers automatically
2. `ResearchAgent` reads and summarises the new file
3. `BlogAgent` drafts a post and saves it to Supabase as a draft
4. `LinkedInAgent` queues 3–5 LinkedIn posts derived from the blog
5. `VideoAgent` generates a 60-second Higgsfield video script

You review the drafts in Supabase, approve, and the scheduler publishes them.

---

## Environment Variables

See `.env.example` for the full list. Required:

- `ANTHROPIC_API_KEY`
- `LINKEDIN_ACCESS_TOKEN` + `LINKEDIN_PERSON_URN`
- `HIGGSFIELD_API_KEY`
- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
- `GITHUB_TOKEN` (for reading Brain-LLM-Fine-Tuning)
