from __future__ import annotations

import asyncio

import httpx

import main


def test_mcp_registers_expected_tools() -> None:
    tools = asyncio.run(main.mcp.list_tools())

    assert [tool.name for tool in tools] == [
        "plan_rush_gift",
        "recommend_gifts",
        "find_pickup_options",
        "draft_gift_message",
    ]


def test_mcp_plan_rush_gift_tool_returns_structured_result() -> None:
    _content, structured = asyncio.run(
        main.mcp.call_tool(
            "plan_rush_gift",
            {
                "origin": "강남역",
                "destination": "판교역",
                "relationship": "여자친구",
                "occasion": "생일",
                "budget_krw": 30_000,
                "minutes_until_meeting": 35,
                "preferences": "꽃 디저트",
                "limit": 1,
            },
        )
    )

    assert structured["recommendations"][0]["gift"]["name"] == "미니 꽃다발"
    assert structured["recommendations"][0]["pickup"]["route"]["feasible"] is True


def test_http_health_route() -> None:
    async def request_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.mcp.streamable_http_app())
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get("/health")

    response = asyncio.run(request_health())

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["name"] == "오다 주웠다"
    assert response.json()["mcp_path"] == "/mcp"
