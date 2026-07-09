# Provider Replacement Plan

## Current MVP

```text
FixtureGiftProvider
FixturePickupStoreProvider
MockRouteProvider
```

These providers are deterministic and require no network, API key, login, or
external data contract.

## Future Kakao Gift Provider

Possible responsibilities:

- Search gift products by category, budget, and occasion.
- Check pickup eligibility.
- Return product URL or purchase path, if allowed.
- Return stock/confidence metadata.

Important:

- Do not scrape Kakao Gift pages.
- Use only official APIs/MCPs or approved partner endpoints.
- Clearly distinguish live data from sample data.

## Future Kakao Local Provider

Possible responsibilities:

- Convert address/place names to coordinates.
- Search nearby pickup stores or brand locations.
- Normalize Korean location names.

Candidate Kakao API:

- Kakao Local REST API

## Future Kakao Mobility Route Provider

Possible responsibilities:

- Estimate direct route duration.
- Estimate origin -> pickup -> destination duration.
- Return detour time and feasibility.

Candidate Kakao API:

- Kakao Mobility Directions API

## Web Search Provider

Use only if Kakao commerce data is unavailable.

Possible responsibilities:

- Search gift ideas by occasion.
- Fetch public product candidates from approved sources.
- Return source URLs.

Risks:

- Search results are noisy.
- Stock and pickup availability may be unreliable.
- Scraping/terms risk must be checked source by source.

## Config

Provider selection should be environment-driven.

```text
RUSH_GIFT_GIFT_PROVIDER=fixture
RUSH_GIFT_PLACE_PROVIDER=fixture
RUSH_GIFT_ROUTE_PROVIDER=mock
```

Future:

```text
RUSH_GIFT_GIFT_PROVIDER=kakao
RUSH_GIFT_PLACE_PROVIDER=kakao_local
RUSH_GIFT_ROUTE_PROVIDER=kakao_mobility
```
