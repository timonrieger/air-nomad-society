# TODO

The rework is merged as-is; this is the iteration list. Background and the
original phase planning live in [refactor-plan.md](refactor-plan.md).

## Design

- [ ] Align web and email design. Today they only share the accent purple
      (`#7747ff`): the site is dark system-sans, the emails are light serif.
      Define one small shared set of tokens (accent, one gray scale, one font
      stack) and apply it to both emails.
- [ ] Redesign `digest.html.j2` from those tokens — it is still the legacy
      40KB table markup (incl. baked-in Dark Reader artifacts), kept
      byte-compatible during the rework on purpose.
- [ ] Restyle `confirm.html.j2` to match.

## Code

- [ ] Simplify and clean up:
  - [ ] `SelectMenu.svelte` duplicates the single/multiple branches almost 1:1
  - [ ] decide on a `GET /` response (currently 404 by choice)
  - [ ] move the confirmation send out of the request path (background task)
        so `POST /subscribe` doesn't block on SMTP
  - [ ] test fixtures repeat subscriber/deal builders across files
  - [ ] revisit CORS for `vite preview` (only the dev-server origin is allowed)

## Features

- [ ] Multiple departure cities per subscriber (`User 1..N Subscription`
      schema rewrite + data migration)
- [ ] Custom email cadence per subscriber (needs more frequent dispatch than
      the weekly cron)
- [ ] Configurable number of favorites and gems (drop the hardcoded 5)
- [ ] More than one deal per country
- [ ] Region/continent grouping for the exclusion picker (needs city→country
      →region reference data; `data.json` cities carry no country today)
- [ ] Less repetitive deals: `SentDeal` history to downweight recent
      destinations, city-level search, shared result cache
- [ ] Second flight provider (e.g. Amadeus) behind `FlightProvider` — Tequila
      access is invitation-only and cannot be re-provisioned if lost

## AI

- [ ] Deal refinement loop: instead of one search per destination, let an
      agent judge candidate deals against the subscriber's context (preferences,
      past sends, season) and re-search with adjusted queries, iterating until
      the context/result match is good enough.
- [ ] Trip planner: turn a free-text trip idea into an actionable multi-city
      itinerary over the flight search (async job, streamed to the UI).
