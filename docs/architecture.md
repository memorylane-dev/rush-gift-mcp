# Architecture

## Design Goal

The server must work without Kakao-specific gift APIs today, while keeping a
clean replacement path for future Kakao MCP/API integration.

## Boundary

```text
AI Client / PlayMCP
  calls MCP tools
Rush Gift MCP
  parses tool arguments
  orchestrates recommendation workflow
Providers
  return gifts, stores, route estimates
Data Sources
  fixture JSON today
  Kakao / web / database later
```

## Modules

```text
rush_gift/
  models.py
    Typed request/response models

  scoring.py
    Gift and pickup ranking logic

  services.py
    Use-case orchestration

  providers/
    base.py
      Provider protocols/interfaces

    fixture.py
      JSON-backed initial providers

    kakao.py
      Future Kakao provider placeholders

    web_search.py
      Future search provider placeholders
```

## Provider Interfaces

### GiftProvider

```python
class GiftProvider(Protocol):
    def search_gifts(self, criteria: GiftCriteria) -> list[Gift]:
        ...
```

Responsibilities:

- Return candidate gifts.
- Include price, category, tags, constraints, and fallback notes.
- Avoid deciding final route feasibility.

### PickupStoreProvider

```python
class PickupStoreProvider(Protocol):
    def find_stores(self, gift_ids: list[str], area: SearchArea) -> list[PickupStore]:
        ...
```

Responsibilities:

- Return stores where gifts can be picked up.
- Include opening time, preparation time, stock confidence, and coordinates.

### RouteProvider

```python
class RouteProvider(Protocol):
    def estimate_route(self, origin: Location, destination: Location, waypoint: Location | None) -> RouteEstimate:
        ...
```

Responsibilities:

- Estimate direct route and route via pickup store.
- Return additional duration and arrival feasibility.

## Scoring

Each final recommendation receives a transparent score.

```text
final_score =
  occasion_fit
  + relationship_fit
  + budget_fit
  + pickup_feasibility
  + time_margin
  + reliability
  - risk_penalty
```

The response should explain why the top recommendation won.

## Data Provenance

All MVP responses must include source/provenance metadata:

```text
source: fixture
stock_status: simulated
route_status: estimated
```

This prevents users and reviewers from mistaking sample data for live Kakao
commerce data.

## Future Kakao Replacement

When official Kakao APIs/MCPs become available:

- Replace `FixtureGiftProvider` with `KakaoGiftProvider`.
- Replace `FixturePickupStoreProvider` with Kakao Gift pickup/store source or Kakao Local.
- Replace `MockRouteProvider` with Kakao Mobility Directions.
- Keep MCP tool schemas stable if possible.

## Privacy

The MVP should not persist:

- user location
- destination
- relationship details
- recipient details
- conversation text

Request data is used only in-memory during tool execution.
