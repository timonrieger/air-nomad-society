# Air Nomad Society

Air Nomad Society is a platform that allows you to get the best flight deals directly in your inbox, fully automated, just one email per week.

## Architecture

- `src/app.py` — Flask web app (subscribe / update / unsubscribe), deployed on Vercel
- `ans/` — the typed core: settings, flight providers, selection, email rendering, and the digest job
- `.github/workflows/digest.yml` — sends the weekly digest (Mondays 05:00 UTC)

The refactor toward FastAPI + SvelteKit is planned in [docs/refactor-plan.md](docs/refactor-plan.md).

## Development

Requires [mise](https://mise.jdx.dev). It installs the pinned Python and uv versions and exposes every project command as a task.

```bash
mise run setup            # install dependencies + pre-commit hooks
docker compose up -d      # local Postgres + Redis
cp .env.example .env      # then fill in values

mise run test             # pytest
mise run lint             # all pre-commit hooks
mise run digest           # run the digest job once
mise run db-upgrade       # apply database migrations
```

The digest sends real emails when SMTP is configured; set `ENVIRONMENT=dev` and `MY_UUID=<your subscriber id>` to restrict it to yourself.

## Migrations

Alembic owns the `air_nomads` table (`alembic/`). A fresh database is created with `mise run db-upgrade`; a database that predates the migrations is adopted **once** with `uv run alembic stamp 0001`, after which `db-upgrade` applies everything newer. Autogenerate a revision after model changes with `mise run db-revision -- -m "message"`.
