# Air Nomad Society

Personalized flight deals delivered to your inbox — fully automated, one email per week.

- `src/app/` — FastAPI JSON API (subscribe / update / unsubscribe via stateless JWT links), deployed on Vercel; interactive docs at `/docs`
- `src/app/cli.py` — the digest job; `.github/workflows/digest.yml` runs it weekly (Mondays 05:00 UTC)
- `alembic/` — migrations for the `air_nomads` table this repo owns
- `src/web/` — SvelteKit frontend, prerendered to static files, calls the API from the browser via `VITE_API_URL`

## Development

Requires [mise](https://mise.jdx.dev) and a Postgres reachable via `DB_URI`. Every project command is a mise task — `mise tasks` lists them all.

```bash
mise run setup       # install dependencies + pre-commit hooks
cp .env.example .env # then fill in values
mise run db-upgrade  # apply database migrations
```

One `.env` at the repo root drives everything locally (backend directly, frontend via vite's `envDir`). The digest sends real emails when SMTP is configured; set `ENVIRONMENT=dev` and `MY_UUID=<your subscriber id>` to restrict it to yourself.

## Deployment

The same variables from `.env.example` live in three places:

| Where | Variables |
|---|---|
| Vercel — API project | `DB_URI`, `SECRET_KEY`, `PUBLIC_BASE_URL`, `SMTP_*` (confirmation emails are sent by the API) |
| Vercel — web project (root `src/web`) | `VITE_API_URL` (baked at build time) |
| GitHub Actions — digest | secrets `DB_URI`, `SECRET_KEY`, `TEQUILA_API_KEY`, `SMTP_*`, `MY_UUID`; repository **variable** `PUBLIC_BASE_URL` |

`PUBLIC_BASE_URL` is the frontend origin — the API's CORS allow-list and the base for all links in emails. `VITE_API_URL` is where the browser reaches the API.

A database that predates the migrations is adopted **once** with `uv run alembic stamp 0001`; after that `mise run db-upgrade` applies everything newer.
