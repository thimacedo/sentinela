create table fallback_logs (
    id uuid primary key default uuid_generate_v4(),
    timestamp timestamptz default now(),
    provider text not null,
    status text not null,
    payload jsonb
);
