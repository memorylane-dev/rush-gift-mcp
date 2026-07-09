# PlayMCP Submission Plan

## Platform Notes

PlayMCP exposes approved MCP servers through a public catalog and lets users add
servers to a toolbox. The registered MCP server needs a name, description, tool
list, starter messages, auth configuration, and an HTTP/HTTPS MCP endpoint.

Observed registration constraints:

- MCP name: up to 30 characters
- MCP identifier: English letters/numbers, up to 16 characters
- MCP description: up to 500 characters
- Starter messages: 3 examples, each up to 40 characters
- Representative image: 600x600 px or larger, png/jpg/jpeg/gif
- Endpoint: `https://` or `http://`, validated by "정보 불러오기"
- Auth options: none, key/token, OAuth

## Registration Copy

### MCP Name

```text
오다 주웠다
```

### MCP Identifier

```text
rushGift
```

### MCP Description

```text
약속 장소로 가는 길에 급하게 선물이 필요할 때, 출발지·목적지·남은 시간·예산·관계·상황을 바탕으로 지금 픽업 가능한 선물 후보와 매장을 추천합니다. 후보별 적합도, 경유 시간, 도착 가능성, 실패 리스크, 짧은 선물 메시지를 함께 제공합니다. 현재는 샘플 데이터 기반 MVP이며 실시간 재고·결제·예약을 보장하지 않습니다.
```

### Starter Messages

```text
강남역에서 판교 가는 길 선물 추천해줘
상사 집들이 선물 2만원 이하로 추천해줘
기념일 선물 픽업 가능한 곳 찾아줘
```

### Auth

MVP: 인증 사용하지 않음.

Reasoning:

- No purchase or payment.
- No account-specific Kakao gift inventory.
- No persistent user profile.
- User-provided location and relationship context are used only for the current request.

Future versions can add OAuth or key/token auth if real commerce APIs, user
purchase history, or saved preferences are introduced.

## Public Positioning

### One-Liner

```text
약속 장소로 가는 길에 지금 픽업 가능한 선물과 경로를 추천합니다.
```

### Longer Pitch

```text
급한 약속 직전에 빈손으로 가기 어려운 상황을 해결합니다. AI가 사용자의 관계, 상황, 예산, 남은 시간을 이해하고, MCP 도구가 선물 후보와 픽업 가능한 매장, 경유 추가 시간을 계산합니다. 사용자는 단순 추천이 아니라 "지금 실제로 가능한 선택지"를 받습니다.
```

## Review-Safe Scope

This MVP does not:

- Scrape Kakao Gift pages.
- Claim real-time Kakao Gift stock.
- Process payments.
- Store sensitive personal information.
- Automatically contact recipients.

This MVP does:

- Use curated sample gift and store data.
- Return clear mock/fixture provenance.
- Separate providers so official Kakao APIs/MCPs can replace fixture data later.
- Provide practical, testable MCP tools.

## Representative Image Direction

Generated asset:

```text
assets/playmcp-representative.png
```

Format: PNG, 1254x1254 px.

Create a simple 600x600 icon:

- Dark background matching PlayMCP's catalog tone.
- Yellow gift box marker on a route line.
- Small clock or pin to signal urgency and pickup.
- No Kakao logo unless explicit permission is available.

Suggested text-free visual concept:

```text
gift box + route pin + clock
```

## Endpoint Plan

Local development can use MCP Inspector over stdio. PlayMCP submission should use
the Streamable HTTP MCP endpoint exposed by the deployed server.

Target endpoint shape:

```text
https://<cloud-host>/mcp
```

Local HTTP check:

```bash
MCP_TRANSPORT=streamable-http FASTMCP_HOST=127.0.0.1 PORT=8000 uv run python main.py
curl http://127.0.0.1:8000/health
```

Deployment runtime:

```text
MCP_TRANSPORT=streamable-http
FASTMCP_HOST=0.0.0.0
PORT=<platform provided port>
MCP_HTTP_PATH=/mcp
```

Deployment candidates:

- Kakao-provided cloud, if available during the contest
- Cloud Run / Fly.io / Render / Railway as fallback
- Dockerized Python app

## Tool List For PlayMCP Preview

```json
{
  "tools": [
    {
      "name": "plan_rush_gift",
      "description": "Plan a last-minute gift pickup route using origin, destination, deadline, budget, relationship, and occasion."
    },
    {
      "name": "recommend_gifts",
      "description": "Recommend gift candidates based on relationship, occasion, budget, preferences, and constraints."
    },
    {
      "name": "find_pickup_options",
      "description": "Find pickup stores for selected gift candidates and estimate detour feasibility."
    },
    {
      "name": "draft_gift_message",
      "description": "Draft a short message for the selected gift, relationship, occasion, and tone."
    }
  ]
}
```
