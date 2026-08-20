# Air Nomad Society — Refactor Plan

Status: planning. Supersedes the ad-hoc todo list in the original notes.

## Decisions

| Question | Decision |
|---|---|
| Where Phase 0/1 runs | GitHub Actions (cron + CI) + managed Postgres (Neon/Supabase free tier) + Vercel for API/web. **No VM required.** |
| Flight data provider | Tequila key still works. Build the `FlightProvider` protocol anyway; Tequila is *an* adapter, not *the* implementation. |
| First slice | Phase 0 foundations. |
| Flask | Cut to FastAPI in Phase 1. No dual-framework period. |

### Why not Vercel Cron

Investigated and rejected. Vercel Hobby allows 2 cron jobs, **minimum cadence once per day**, UTC only, with firing time guaranteed only within the hour, and a 10s default function ceiling. The current job is `users × ~200 countries` of sequential HTTP with 10s sleep-retries, and per-subscription schedules (gap 4) need at least hourly dispatch. Not viable.

GitHub Actions scheduled workflows allow cron down to every 5 minutes with a 6-hour job limit, free for public repos, and are the same system needed for CI/CD.

---

## Current state

Two entrypoints that are tangled together:

- `src/app.py` — Flask + WTForms + Bootstrap on Vercel serverless. Token-in-URL identity, no accounts.
- `src/main.py` — the weekly batch job. A bare script: no functions, no `if __name__`, no error handling, runs at import.

`src/data_manager.py:1` imports `src.app`, so the batch job boots Flask, Bootstrap5, CSRF and runs `create_all()` just to open a DB session.

### Defects to fix in Phase 0

1. **`src/notification_manager.py`** builds each email by appending HTML to one shared file (`templates/send_email.html`), sending, then truncating. Process-global mutable state — concurrent users produce interleaved emails, and it fails on a read-only filesystem. Hardest blocker to parallelism.
2. **`src/flight_data.py:6-13`** — trailing commas make `price`, `departure_city`, `from_date` etc. 1-tuples instead of scalars. Worked around throughout `main.py` as `flight.price[0]`.
3. **`src/main.py:30-38`** — gem de-duplication `break`s the *outer* loop after the first replacement; remaining gems colliding with favourite countries are never swapped.
4. **`src/flight_search.py`** — duplicated `FlightData` construction across two branches; `route[2]["aTime"]` assumes exactly 3 legs; no request timeouts; blocking `time.sleep(10)` retries.
5. **`src/utility/constants.py:18`** — `int(os.getenv("SMTP_PORT"))` raises `TypeError` at import when unset.
6. **`src/app.py`** — `@cache.cached(timeout=52 weeks)` with `SimpleCache` on serverless is per-instance memory, effectively a no-op. `create_all()` runs on every cold start.
7. **`Procfile`** references `app:app`; the module is `src.app`.

---

## Functional gaps → architectural demands

| Gap | Requires |
|---|---|
| 1. Single origin city | Schema: `User 1..N Subscription` |
| 4. Fixed weekly cadence | Per-subscription schedule + hourly dispatcher |
| 5. Only 5 favourites | Config column |
| 6. One flight per country | Config column + search fan-out |
| 2. Country exclusion UX | Region/continent reference data + real multi-select widget |
| 3. Same city every week | City-level search + sent-deal history + shared cache |
| 7. AI itinerary planner | Async jobs, streaming, structured output, minutes-long runs |

Gaps 1, 4, 5, 6 collapse into one change: replace the one-row-per-user model with `Subscription` as a first-class entity owning origins, filters, limits and schedule.

Gap 3 is structural, not random. `one_for_city: 1` plus per-country search returns the single cheapest destination in each country, and the cheapest city in Finland does not change week to week. Fix requires city-granularity search plus a `SentDeal` history table to downweight recent destinations. This multiplies API calls ~10x, which is why caching on `(origin, destination, date_window, nights)` is architecture rather than optimisation — every user sharing an origin shares the searches.

Gap 7 is the only item that genuinely requires FastAPI + workers + Svelte.

---

## Target shape

Revised in Phase 1: instead of an apps/packages monorepo, `src` is the import
root of a single conventional FastAPI layout (SvelteKit joins later as a
sibling directory; workers become new entrypoints over the same services):

```
src/
  main.py     FastAPI app (Vercel auto-detects), security headers, routers
  config.py   pydantic-settings
  db.py       SQLAlchemy 2.0 models (vendored), engine, session
  cli.py      digest entrypoint (GitHub Actions cron)
  routers/    subscription API
  services/   domain logic: refdata, selection, digest, emails, mailer,
              tokens (JWT links), providers (FlightProvider protocol)
  models/     pydantic domain models
alembic/      migrations, URL from src.config
```

### The seam that makes migration cheap

Jobs stay transport-agnostic:

```python
# packages/core/jobs.py
async def run_digest(sub_id: UUID, deps: Deps) -> DigestResult: ...
```

- **Now:** GitHub Actions cron → `python -m src.cli digest`
- **Later:** `@dramatiq.actor` wrapping the identical function

Moving from Actions to dramatiq workers becomes a new entrypoint file, not a rewrite. Same principle for `FlightProvider` — swapping Tequila for Amadeus touches one adapter.

---

## Phase 0 — foundations (no infra, nothing user-visible)

Flask keeps running on Vercel throughout. Cron moves to GitHub Actions.

- [x] `pyproject.toml` + `uv`, replacing `requirements.txt`
- [x] ruff + ty + pre-commit hooks (mirroring immichpy's stack)
- [x] GitHub Actions CI: lint, typecheck, test on PR
- [x] `pydantic-settings` config — no import-time crashes, `.env.example`
- [x] `FlightProvider` protocol + `TequilaProvider` + `FakeProvider`
- [x] Fix `FlightData` tuple bug; convert to a pydantic model
- [x] Extract `main.py` logic into pure, tested functions (selection)
- [x] Rewrite emails as a Jinja template — removes the shared-file bug
      (byte-verified against the legacy output)
- [x] Break the digest job's dependency on `src.app`
- [x] `python -m ans.cli digest` entrypoint
- [x] GitHub Actions scheduled workflow replacing the current cron
      (`digest.yml`, Mondays 05:00 UTC; needs the secrets listed there)
- [x] `docker-compose.yml` for local dev (Postgres, Redis)
- [x] Request timeouts, structured logging, per-user error isolation

Exit criteria met: the weekly digest runs from GitHub Actions, selection and
digest logic are tested against `FakeProvider`, and CI is green on PRs.

Left deliberately out of Phase 0: ranking/diversity logic (needs the
`SentDeal` table, Phase 1) and fixing `src/app.py`'s type errors (the file is
replaced by FastAPI in Phase 1; it stays the only `ty` exclusion).

## Phase 1 — API-first port (done)

Scope was revised during implementation: structural port first, UI allowed to
break until Svelte, identity via stateless JWTs instead of stored tokens or
magic links.

- [x] FastAPI replaces Flask — pure JSON API (`/subscribe`, `/subscription`,
      `/unsubscribe`), `/docs` as the interim UI
- [x] Alembic, plain setup (the shared DB now holds only `air_nomads`);
      baseline 0001 + 0002 drops the token column
- [x] `database-service` vendored: this repo owns the `AirNomads` model,
      engine and session plumbing
- [x] Stateless JWT email links (HS256 over SECRET_KEY, `sub` + `action`
      claims, no expiry) — old token links are dead by design
- [x] `src` becomes the import root: `routers/` + `services/` + `models/`

Deferred from the original Phase 1 list:

- [ ] `User 1..N Subscription` schema rewrite + migration of existing rows
- [x] SvelteKit on Vercel (prebuilt static site under src/web; landing +
      subscription pages, bits-ui + Tailwind, JWT links handled client-side)
- [ ] Continent/region reference data for the exclusion UX
- [ ] `SentDeal` history table + city-level search + Redis result cache

The schema rewrite still ships gaps 1, 4, 5, 6; gap 2/3 items follow it.

## Phase 2 — infra

- [ ] Docker Compose in anger: Postgres, Redis, api, worker, scheduler, Caddy
- [ ] dramatiq + periodiq replace the Actions cron
- [ ] Deploy target: dedicated ~€4/mo VPS

Do **not** co-locate with private apps (Immich, Jellyfin). A separate VPS buys clean blast-radius separation and keeps the media box's ports closed. The value here is not cost saving — it is enabling gap 7.

## Phase 3 — AI itinerary planner

Async job + status polling, SSE streaming to the UI, structured output for the itinerary schema, LLM tool-use over the flight search. Per-user rate limits and caching for cost control.

---

## Risks

- **Tequila access.** Kiwi has moved Tequila to invitation-only for new partners. Existing keys work, but access cannot be re-provisioned if lost. Mitigated by the provider protocol; Amadeus Self-Service is the most likely fallback.
- **Reference data quality.** `static/data.json` cities carry no country field, so cities cannot currently be grouped by country — required for gaps 2 and 3. Needs a proper dataset.
- **Email deliverability.** Raw SMTP is fragile for a mailing product. Consider Resend/Postmark free tiers.
- **CORS/cookies** once web and API are on different origins. Either scope cookies to `.timonrieger.de` via an `api.` subdomain, or proxy through SvelteKit server routes.
- ~~**`database-service` git dependency.**~~ Resolved in Phase 1: the schema is vendored and Alembic-managed in this repo; the git dependency is gone.
