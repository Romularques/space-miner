create table public.leaderboard (
  id bigint generated always as identity primary key,
  initials char(3) not null check (initials ~ '^[A-Z]{3}$'),
  score integer not null check (score between -999999 and 999999),
  phase integer not null check (phase between 1 and 999),
  created_at_ms bigint not null
);

create index leaderboard_ranking_idx
  on public.leaderboard (score desc, phase desc, created_at_ms desc);

alter table public.leaderboard enable row level security;

-- Não conceda SELECT/INSERT para anon ou authenticated: só a Edge Function acessa a tabela.
