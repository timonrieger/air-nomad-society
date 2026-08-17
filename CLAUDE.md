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

- `src/app.py` — Flask web app (subscribe / update / unsubscribe), deployed on Vercel
- `src/main.py` — the digest job that searches flights and sends the emails
- `static/data.json` — reference data: countries, cities, currencies, per-country image URLs

The refactor currently underway is planned in `docs/refactor-plan.md`. The legacy `src/`
tree is excluded from `ty` until Phase 0 migrates it module by module; drop those
exclusions as you go rather than adding new ones.
