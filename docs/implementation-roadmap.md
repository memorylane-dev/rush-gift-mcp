# Implementation Roadmap

## Phase 0: Repo And Docs

Status: planned

- Create standalone repository.
- Add PlayMCP submission copy.
- Add architecture and provider replacement plan.
- Add demo scenarios.

## Phase 1: Fixture-Backed MCP

Goal: local MCP Inspector demo.

Tasks:

- Add Python project using `mcp[cli]`.
- Define models for gift, store, route, and recommendation.
- Create `data/gifts.json`.
- Create `data/stores.json`.
- Implement fixture providers.
- Implement scoring.
- Implement MCP tools:
  - `plan_rush_gift`
  - `recommend_gifts`
  - `find_pickup_options`
  - `draft_gift_message`
- Add focused unit tests.

Acceptance:

- `uv run mcp dev main.py` shows all tools.
- Demo prompt returns 3 ranked recommendations.
- Recommendations include gift, store, detour time, risk, and message.

## Phase 2: HTTP Endpoint

Goal: PlayMCP-compatible endpoint.

Tasks:

- Run MCP over HTTP-compatible transport.
- Add Dockerfile.
- Add health check endpoint if required by hosting platform.
- Add deployment config.
- Confirm PlayMCP "정보 불러오기" can retrieve tools.

Acceptance:

- Public `https://.../mcp` endpoint is reachable.
- PlayMCP registration loads tool list.

## Phase 3: Quality Polish

Goal: make the demo feel complete.

Tasks:

- Improve sample data coverage for Seoul/Pangyo scenarios.
- Add response formatting guidelines.
- Add explicit provenance in every result.
- Add error messages for impossible schedules.
- Add fallback recommendations when no pickup is feasible.

Acceptance:

- Demo works for at least 5 scenarios.
- Failure cases are useful, not generic.

## Phase 4: Optional Real API Providers

Goal: replace mock data gradually.

Tasks:

- Add Kakao Local place/address search provider.
- Add Kakao Mobility route provider.
- Add web search provider for gift discovery.
- Keep fixture provider available for deterministic demos.

Acceptance:

- Provider can be switched through environment config.
- Tests still run without network access.

## Day-One MVP Scope

Build only this:

```text
fixture data + scoring + 4 MCP tools + README demo
```

Avoid:

- payment
- login
- live stock claims
- Kakao page scraping
- personalized history

## Definition Of Done For First Demo

Given:

```text
지금 강남역에서 판교역으로 여자친구 생일 약속 가는 중이야.
30분 안에 도착해야 하고 예산은 3만원이야.
가는 길에 픽업 가능한 선물 추천해줘.
```

The server returns:

- top 3 recommendations
- gift name and price
- pickup store
- estimated pickup preparation time
- estimated detour time
- whether arrival is feasible
- why it fits the relationship and occasion
- short message
- fixture/mock provenance
