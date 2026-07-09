from __future__ import annotations

import asyncio

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
