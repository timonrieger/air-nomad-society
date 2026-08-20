# Air Nomad Society

Air Nomad Society is a platform that allows you to get the best flight deals directly in your inbox, fully automated, just one email per week.

## Architecture

- `src/app/main.py` — FastAPI JSON API (subscribe / update / unsubscribe via stateless JWT links), deployed on Vercel; interactive docs at `/docs`
- `src/app/services/` — domain logic: flight providers, selection, email rendering, JWT tokens
- `src/app/cli.py` — the digest job; `.github/workflows/digest.yml` runs it weekly (Mondays 05:00 UTC)
- `alembic/` — migrations for the `air_nomads` table this repo owns
- `src/web/` — SvelteKit frontend (landing + subscription pages; bits-ui + Tailwind), prerendered to static files, calls the API from the browser via `VITE_API_URL`

See [docs/refactor-plan.md](docs/refactor-plan.md) for the refactor roadmap.

## Development

Requires [mise](https://mise.jdx.dev). It installs the pinned Python and uv versions and exposes every project command as a task.

```bash
mise run setup            # install dependencies + pre-commit hooks
docker compose up -d      # local Postgres + Redis
cp .env.example .env      # then fill in values

mise run dev              # API dev server (uvicorn, port 8000)
mise run web-dev          # SvelteKit dev server (pnpm)
mise run test             # pytest
mise run lint             # all pre-commit hooks
mise run digest           # run the digest job once
mise run db-upgrade       # apply database migrations
```

The digest sends real emails when SMTP is configured; set `ENVIRONMENT=dev` and `MY_UUID=<your subscriber id>` to restrict it to yourself.

## Environments

One `.env` at the repo root drives everything locally (backend directly, frontend via vite's `envDir`); `.env.example` documents the localhost values. In deployment the same variables live in three places:

| Where | Variables |
|---|---|
| Vercel — API project | `DB_URI`, `SECRET_KEY`, `PUBLIC_BASE_URL`, `SMTP_EMAIL`, `SMTP_PWD`, `SMTP_SERVER`, `SMTP_PORT` (confirmation emails are sent by the API) |
| Vercel — web project (root `src/web`) | `VITE_API_URL` (baked at build time) |
| GitHub Actions — digest | secrets `DB_URI`, `SECRET_KEY`, `TEQUILA_API_KEY`, `SMTP_*`, `MY_UUID`; repository **variable** `PUBLIC_BASE_URL` |

`PUBLIC_BASE_URL` is the frontend origin — it is both the API's CORS allow-list and the base for all links in emails. `VITE_API_URL` is where the browser reaches the API.

## Migrations

Alembic owns the `air_nomads` table (`alembic/`). A fresh database is created with `mise run db-upgrade`; a database that predates the migrations is adopted **once** with `uv run alembic stamp 0001`, after which `db-upgrade` applies everything newer. Autogenerate a revision after model changes with `mise run db-revision -- -m "message"`.
