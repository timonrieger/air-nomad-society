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

- `ans/` — the typed core: settings, providers, selection, email rendering, digest CLI
- `src/app.py` — Flask web app (subscribe / update / unsubscribe), deployed on Vercel
- `static/data.json` — reference data: countries, cities, currencies, per-country image URLs
- `ans/templates/digest.html.j2` — the email; kept byte-identical to the legacy markup,
  excluded from whitespace fixers

The refactor currently underway is planned in `docs/refactor-plan.md`. `src/app.py` is
the only remaining `ty` exclusion; it is replaced in Phase 1, don't add new exclusions.
