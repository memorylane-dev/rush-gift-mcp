# 오다 주웠다 MCP

<img src="assets/playmcp-representative.png" alt="오다 주웠다 representative image" width="120" />

약속 장소로 이동 중인 사용자를 위해 지금 살 수 있는 선물과 픽업 동선을 추천하는
PlayMCP 제출용 MCP 서버 프로젝트입니다.

## Concept

**"오다 주웠다처럼 자연스럽게 건넬 수 있도록, AI가 선물 후보와 픽업 경로를 한 번에 짜주는 MCP"**

사용자는 출발지, 목적지, 도착 제한 시간, 예산, 관계, 상황을 자연어로 말합니다.
AI는 이 MCP의 도구를 호출해 선물 후보, 픽업 매장, 경유 추가 시간, 실패 리스크,
짧은 메시지를 함께 제안합니다.

## Why MCP

일반 AI 답변은 "좋아 보이는 선물"을 말할 수 있지만, 지금 상황에서 실제로
들를 수 있는지 판단하지 못합니다. 이 MCP는 추천을 다음 데이터와 계산으로 검증합니다.

- 선물 후보 데이터
- 픽업 가능 매장 데이터
- 출발지-매장-목적지 경유 시간
- 약속 시간까지 남은 여유
- 관계/상황/예산별 실패 리스크

## Current Strategy

카카오 선물하기 MCP/API가 없더라도 동작하도록 fixture provider로 시작합니다.
나중에 카카오 연동이 가능해지면 provider 구현만 교체합니다.

```text
MCP Tools
  -> RushGiftService
    -> GiftProvider
    -> PickupStoreProvider
    -> PlaceProvider
    -> RouteProvider
```

초기 provider:

- `FixtureGiftProvider`: 샘플 선물 데이터
- `FixturePickupStoreProvider`: 샘플 픽업 매장 데이터
- `MockRouteProvider`: 좌표 기반 경유 시간 추정

교체 대상 provider:

- `KakaoGiftProvider`
- `KakaoLocalProvider`
- `KakaoMobilityRouteProvider`
- `WebSearchGiftProvider`

## Tools

- `plan_rush_gift`: 상황을 받아 추천, 픽업, 경유 시간, 메시지를 한 번에 반환
- `recommend_gifts`: 관계/상황/예산 기준으로 선물 후보 추천
- `find_pickup_options`: 선물 후보별 픽업 매장과 경유 가능성 계산
- `draft_gift_message`: 관계와 상황에 맞는 짧은 카드 메시지 생성

## PlayMCP

Submission endpoint:

```text
https://rush-gift-mcp.vercel.app/mcp
```

Health check:

```text
https://rush-gift-mcp.vercel.app/health
```

PlayMCP gateway:

```text
https://playmcp.kakao.com/mcp
```

The submission endpoint is this server. The PlayMCP gateway is Kakao's proxy for
approved MCP servers in a user's toolbox and requires a PlayMCP access token.

## Demo Prompt

```text
지금 강남역에서 판교역으로 여자친구 생일 약속 가는 중이야.
35분 안에 도착해야 하고 예산은 3만원이야.
가는 길에 픽업 가능한 선물 추천해줘.
```

30분으로 요청하면 현재 샘플 경로 기준으로는 픽업이 어렵다는 fallback을 반환합니다.
이 케이스는 "무조건 추천"이 아니라 불가능한 상황을 솔직하게 말하는 데모로 사용합니다.

## Quick Start

Local MCP Inspector:

```bash
uv sync
uv run mcp dev main.py
```

MCP Inspector가 열리면 다음 도구를 호출할 수 있습니다.

- `plan_rush_gift`: 선물 추천, 픽업 매장, 경유 가능성, 메시지를 한 번에 반환
- `recommend_gifts`: 관계/상황/예산 기준으로 선물 후보 추천
- `find_pickup_options`: 선물 후보별 픽업 매장과 경유 가능성 계산
- `draft_gift_message`: 관계와 상황에 맞는 짧은 카드 메시지 생성

stdio 서버로 직접 실행할 때:

```bash
uv run python main.py
```

HTTP MCP endpoint로 실행할 때:

```bash
MCP_TRANSPORT=streamable-http FASTMCP_HOST=127.0.0.1 PORT=8000 uv run python main.py
```

Local URLs:

- MCP endpoint: `http://127.0.0.1:8000/mcp`
- Health check: `http://127.0.0.1:8000/health`

Docker:

```bash
docker build -t rush-gift-mcp .
docker run --rm -p 8000:8000 rush-gift-mcp
```

Vercel:

```bash
npx vercel
```

After deployment, use:

```text
https://<production-domain>/mcp
```

If PlayMCP cannot load tools from the Vercel URL, deploy the same code to a
container/always-on host with the Dockerfile.

테스트:

```bash
uv run pytest
```

## Documentation

- [PlayMCP Submission Plan](docs/playmcp-submission.md)
- [Architecture](docs/architecture.md)
- [Implementation Roadmap](docs/implementation-roadmap.md)
- [Demo Scenarios](docs/demo-scenarios.md)
- [Deployment](docs/deployment.md)

## Development Status

Implemented:

- fixture-backed gift, place, store, and route providers
- transparent scoring for gift fit and pickup feasibility
- four MCP tools in `main.py`
- unit tests for recommendation, fallback, budget filtering, pickup options, and MCP tool registration

Next:

- deploy the Dockerized HTTP MCP server
- replace fixture providers with Kakao/web providers when available
