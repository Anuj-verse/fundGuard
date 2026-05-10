Postgres persistence for FundGuard

Overview
--------
This project uses a configurable `DATABASE_URL` environment variable. By default the services use a local SQLite file (`sqlite+aiosqlite:///./risk_engine.db`) for quick testing.

For production-like persistence across containers, run PostgreSQL and set `DATABASE_URL` accordingly for both `risk-engine` and `dashboard-api`.

Example docker-compose snippet:

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: fundguard
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: fundguard
    volumes:
      - pgdata:/var/lib/postgresql/data

Then set `DATABASE_URL` for services:

environment:
  - DATABASE_URL=postgresql+asyncpg://fundguard:secret@postgres:5432/fundguard

Notes
-----
- After changing to Postgres, run migrations or allow the services to auto-create tables at startup (the code will create tables automatically if missing).
- Ensure both `risk-engine` and `dashboard-api` use the same DB URL so the dashboard can read persisted records.
