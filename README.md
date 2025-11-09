# :whale: Docker Compose Intro
Simple `actix-web`-based API with containerization.

## Endpoints
- `/`: respond `Hello, Docker!`.
- `/ping`: respond `pong`, incrementing the number of accesses.
- `/visits`: respond the number of `/ping` accesses.

## Build
Building of lightweight :crab: Rust application image takes two steps: 
1. Build statically-linked `--release` target via `rust-musl-cross`.
2. Copy the binary into `scratch`.

The resulting image is about 11 MB in size.

## Compose
`docker-compose.yml` contains two services: `db` (PostgreSQL) and `app` (`actix-web`-based API):
1. :elephant: PostgreSQL `db` service employs `postgres:16-alpine` based on lightweight Apline Linux. Postgres env is set from local `.env` environment.
The service also initializes database via `init.sql` script, creating the `visits` table:
```sql
create table if not exists visits (
    id serial,
    ip_address text not null,
    created_at timestamp default now(),
    primary key ("id")
);
```
Each 30 seconds Docker Compose employs `pg_isready` :four_leaf_clover: to check whether the database is accepting connections.  
2. `app` service builds the image based on `Dockerfile` after database begins to accept connections (`condition: service_healthy`) and
sets `DATABASE_URL` used in `actix-web` application.

## CI
`test-local.sh` emulates `.github/workflow/test.yml` locally. Run
```bash
chmod +x test-local.sh
./test-local.sh
```
to check whether CI is passed before commiting changes.

Local environment in CI is accessed via GitHub secrets :no_entry:.
