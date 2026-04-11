-- CareerScout AI v2 — Supabase Schema
-- Run this in Supabase → SQL Editor

-- ── Jobs table (stores AI-filtered listings) ────────────────────────────────
create table if not exists jobs (
  id           uuid default gen_random_uuid() primary key,
  title        text not null,
  type         text,              -- internship | hackathon | job
  domain       text,              -- AI/ML | Web Dev | Data Science etc.
  skills       text[],            -- array of required skills
  location     text,
  stipend      text,
  deadline     text,
  score        integer,           -- AI relevance score 0-10
  recommended  boolean default true,
  reasoning    text,              -- AI chain-of-thought explanation
  link         text unique,       -- dedup key
  source       text,              -- Unstop | Devfolio | LinkedIn etc.
  telegram_msg text,              -- pre-generated Telegram message
  created_at   timestamptz default now()
);

-- ── Users table (for multi-user Telegram bot) ───────────────────────────────
create table if not exists users (
  id           uuid default gen_random_uuid() primary key,
  telegram_id  bigint unique not null,
  username     text,
  skills       text[],            -- user's skill preferences
  interests    text[],            -- domains they care about
  active       boolean default true,
  created_at   timestamptz default now()
);

-- ── Indexes for fast queries ─────────────────────────────────────────────────
create index if not exists jobs_score_idx on jobs(score desc);
create index if not exists jobs_type_idx  on jobs(type);
create index if not exists jobs_created_idx on jobs(created_at desc);

-- ── Row Level Security (enable in Supabase dashboard too) ───────────────────
alter table jobs  enable row level security;
alter table users enable row level security;

-- Allow public reads on jobs (for React frontend)
create policy "Public read jobs"
  on jobs for select
  using (true);

-- Allow backend service role to insert/update
create policy "Service insert jobs"
  on jobs for insert
  with check (true);