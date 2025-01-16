-- Create raffles table
create table if not exists public.raffles (
    id bigint primary key generated always as identity,
    title text not null,
    description text,
    ticket_price decimal(10,2) not null,
    total_tickets integer not null,
    tickets_sold integer default 0,
    start_date timestamp with time zone default timezone('utc'::text, now()) not null,
    end_date timestamp with time zone not null,
    is_active boolean default true,
    winner_id uuid references auth.users(id),
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table public.raffles enable row level security;

-- Create policies
create policy "Anyone can view raffles" on public.raffles
    for select using (true);

create policy "Only superusers can insert raffles" on public.raffles
    for insert with check (
        auth.jwt() ->> 'is_superuser' = 'true'
    );

create policy "Only superusers can update raffles" on public.raffles
    for update using (
        auth.jwt() ->> 'is_superuser' = 'true'
    );

create policy "Only superusers can delete raffles" on public.raffles
    for delete using (
        auth.jwt() ->> 'is_superuser' = 'true'
    );

-- Create indexes
create index if not exists raffles_is_active_idx on public.raffles (is_active);
create index if not exists raffles_end_date_idx on public.raffles (end_date);

-- Create function to handle updated_at
create or replace function public.handle_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = timezone('utc'::text, now());
    return new;
end;
$$;

-- Create trigger for updated_at
create trigger set_updated_at
    before update on public.raffles
    for each row
    execute function public.handle_updated_at();
