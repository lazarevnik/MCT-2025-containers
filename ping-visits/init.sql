create table if not exists visits (
    id serial,
    ip_address text not null,
    created_at timestamp default now(),
    primary key ("id")
);
