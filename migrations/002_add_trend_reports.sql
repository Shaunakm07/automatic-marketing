-- Run in your Supabase SQL editor to add trend reporting support

create table if not exists trend_reports (
  id           uuid primary key default gen_random_uuid(),
  report       jsonb not null,
  sources_used text[] not null default '{}',
  created_at   timestamptz not null default now()
);

create index if not exists idx_trend_reports_created_at on trend_reports(created_at desc);

-- Allow approved_at tracking on content_items
alter table content_items add column if not exists approved_at timestamptz;
