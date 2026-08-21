# CLAUDE.md

## Code Style

- Reuse existing code logic wherever possible
- Write assertive, direct code — no defensive abstractions
- Skip error handling unless absolutely necessary
- Type everything extensively
- Keep changes minimal

## Commands

Use `mise` tasks to run all project commands. The root `mise.toml` is the monorepo root (global tasks); package tasks live in `packages/app/mise.toml` and `packages/web/mise.toml` and are addressed as `mise run '//packages/app:<task>'` / `mise run '//packages/web:<task>'`. List everything with `mise tasks --all`.

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

## Project

Air Nomad Society emails personalized flight deals to subscribers.

- `packages/app/` — the Python backend: `pyproject.toml`, `uv.lock`, `.env`, `tests/`, `alembic/` migrations, source in `src/`
- `packages/app/src/main.py` — FastAPI JSON API (the Vercel project's Root Directory is `packages/app`; entrypoint `src.main:app`)
- `packages/app/src/routers/` — endpoints; `src/services/` — domain logic; `src/models/` — pydantic models
- `packages/app/src/db.py` — SQLAlchemy models + engine
- `packages/app/src/cli.py` — the weekly digest job and one-off announcement sends
- `packages/app/src/data.json` — reference data: countries, cities, currencies, per-country image URLs
- `packages/app/src/templates/digest.html.j2` — the digest email; brand tokens are defined once in `packages/app/src/brand.json`
- `packages/web/` — SvelteKit frontend (pnpm, bits-ui, Tailwind v4); fully prerendered static site, browser calls the API directly (`VITE_API_URL` from `packages/web/.env`, CORS on the backend)

Email links are stateless JWTs (`packages/app/src/services/tokens.py`). `packages/app` is the
Python project root and import root (`from src.services import ...`).
