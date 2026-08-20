# CLAUDE.md

## Code Style

- Reuse existing code logic wherever possible
- Write assertive, direct code — no defensive abstractions
- Skip error handling unless absolutely necessary
- Type everything extensively
- Keep changes minimal

## Commands

Use `mise` tasks to run all project commands. See `.mise/config.toml` for all available tasks.

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

## Project

Air Nomad Society emails personalized flight deals to subscribers.

- `src/app/main.py` — FastAPI JSON API (Vercel auto-detects the `app` object)
- `src/app/routers/` — endpoints; `src/app/services/` — domain logic; `src/app/models/` — pydantic models
- `src/app/db.py` — SQLAlchemy models + engine; migrations live in `alembic/`
- `src/app/cli.py` — the weekly digest job (`mise run digest`)
- `src/app/data.json` — reference data: countries, cities, currencies, per-country image URLs
- `src/app/templates/digest.html.j2` — the digest email; brand tokens are defined once in `src/app/brand.json` (loaded by `src/app/services/emails.py`, compiled to Tailwind theme tokens by `src/web/vite.config.ts`)
- `src/web/` — SvelteKit frontend (pnpm, bits-ui, Tailwind v4); fully prerendered static site, browser calls the API directly (`VITE_API_URL`, CORS on the backend)

Email links are stateless JWTs (`src/app/services/tokens.py`). `src` is the import root
(`from src.app.services import ...`). The refactor is planned in `docs/refactor-plan.md`;
there are no `ty` exclusions — keep it that way.
