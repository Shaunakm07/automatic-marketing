-- Run in your Supabase SQL editor before first use

create table if not exists content_items (
  id             uuid primary key default gen_random_uuid(),
  content_type   text not null,      -- blog | linkedin | video_script | research_digest
  title          text not null,
  body           text not null,
  status         text not null default 'draft',  -- draft | published
  metadata       jsonb,
  published_url  text,
  created_at     timestamptz not null default now(),
  published_at   timestamptz
);

create table if not exists content_queue (
  id             uuid primary key default gen_random_uuid(),
  post_text      text not null,
  pillar         text not null,
  status         text not null default 'queued',  -- queued | sent | skipped
  source_id      uuid references content_items(id),
  linkedin_id    text,
  created_at     timestamptz not null default now(),
  scheduled_for  timestamptz,
  sent_at        timestamptz
);

create table if not exists research_digests (
  id               uuid primary key default gen_random_uuid(),
  experiment_name  text not null unique,
  summary          text not null,
  key_findings     jsonb not null default '[]',
  created_at       timestamptz not null default now()
);

-- Indexes for common query patterns
create index if not exists idx_content_items_type_status on content_items(content_type, status);
create index if not exists idx_content_queue_status      on content_queue(status, created_at);
create index if not exists idx_research_digests_name     on research_digests(experiment_name);
