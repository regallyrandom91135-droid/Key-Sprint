-- Run this entire script in Supabase: SQL Editor -> New query -> Run.
create extension if not exists pgcrypto;

create table if not exists public.users (
    id uuid primary key default gen_random_uuid(),
    name text not null check (char_length(name) <= 80),
    email text not null unique,
    password_hash text not null,
    created_at timestamptz not null default now()
);

create table if not exists public.typing_tests (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    passage text not null,
    typed_text text not null default '',
    duration_seconds numeric(8,2) not null,
    wpm numeric(8,1) not null,
    accuracy numeric(5,1) not null,
    correct_words integer not null,
    total_words integer not null,
    notes text not null default '',
    created_at timestamptz not null default now()
);

create index if not exists typing_tests_user_created_idx
on public.typing_tests(user_id, created_at desc);

-- The app accesses Supabase only from the Flask server using the service-role key.
-- Never put the service-role key in HTML, JavaScript, GitHub, or a public environment variable.
alter table public.users enable row level security;
alter table public.typing_tests enable row level security;
