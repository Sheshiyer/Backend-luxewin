-- Create purchases table
create table if not exists public.purchases (
    id bigint primary key generated always as identity,
    user_id uuid references auth.users(id) not null,
    raffle_id bigint references public.raffles(id) not null,
    quantity integer not null,
    total_amount decimal(10,2) not null,
    transaction_id text unique,
    purchase_date timestamp with time zone default timezone('utc'::text, now()) not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table public.purchases enable row level security;

-- Create policies
create policy "Users can view their own purchases" on public.purchases
    for select using (auth.uid() = user_id);

create policy "Users can create their own purchases" on public.purchases
    for insert with check (auth.uid() = user_id);

-- Create indexes
create index if not exists purchases_user_id_idx on public.purchases (user_id);
create index if not exists purchases_raffle_id_idx on public.purchases (raffle_id);
create index if not exists purchases_transaction_id_idx on public.purchases (transaction_id);

-- Create function to update tickets_sold in raffles
create or replace function public.update_raffle_tickets_sold()
returns trigger
language plpgsql
security definer
as $$
begin
    if (tg_op = 'INSERT') then
        update public.raffles
        set tickets_sold = tickets_sold + new.quantity
        where id = new.raffle_id;
        return new;
    elsif (tg_op = 'DELETE') then
        update public.raffles
        set tickets_sold = tickets_sold - old.quantity
        where id = old.raffle_id;
        return old;
    end if;
    return null;
end;
$$;

-- Create trigger for updating tickets_sold
create trigger update_raffle_tickets
    after insert or delete on public.purchases
    for each row
    execute function public.update_raffle_tickets_sold();

-- Create function to validate purchase
create or replace function public.validate_purchase()
returns trigger
language plpgsql
security definer
as $$
declare
    raffle_record record;
begin
    -- Get raffle details
    select * into raffle_record
    from public.raffles
    where id = new.raffle_id;

    -- Check if raffle exists and is active
    if raffle_record is null then
        raise exception 'Raffle not found';
    end if;
    
    if not raffle_record.is_active then
        raise exception 'Raffle is not active';
    end if;

    -- Check if raffle end date has passed
    if raffle_record.end_date < now() then
        raise exception 'Raffle has ended';
    end if;

    -- Check if there are enough tickets available
    if (raffle_record.tickets_sold + new.quantity) > raffle_record.total_tickets then
        raise exception 'Not enough tickets available';
    end if;

    -- Validate total amount
    if new.total_amount != (raffle_record.ticket_price * new.quantity) then
        raise exception 'Invalid total amount';
    end if;

    return new;
end;
$$;

-- Create trigger for purchase validation
create trigger validate_purchase
    before insert on public.purchases
    for each row
    execute function public.validate_purchase();
