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

- `src/main.py` — FastAPI JSON API (Vercel auto-detects the `app` object)
- `src/routers/` — endpoints; `src/services/` — domain logic; `src/models/` — pydantic models
- `src/db.py` — SQLAlchemy models + engine; migrations live in `alembic/`
- `src/cli.py` — the weekly digest job (`mise run digest`)
- `src/data.json` — reference data: countries, cities, currencies, per-country image URLs
- `src/templates/digest.html.j2` — the email; legacy markup, excluded from whitespace fixers

Email links are stateless JWTs (`src/services/tokens.py`). `src` is the import root
(`from src.services import ...`). The refactor is planned in `docs/refactor-plan.md`;
there are no `ty` exclusions — keep it that way.
