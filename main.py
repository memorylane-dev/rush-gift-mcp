from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP

from rush_gift.services import DEFAULT_CURRENT_TIME, create_default_service


mcp = FastMCP(
    "rush-gift",
    instructions=(
        "약속 장소로 이동 중인 사용자에게 지금 픽업 가능한 선물, 경유 시간, "
        "실패 리스크, 짧은 선물 메시지를 추천합니다. 모든 MVP 데이터는 fixture이며 "
        "실시간 재고/결제/예약을 보장하지 않습니다."
    ),
)
service = create_default_service()


@mcp.tool()
def plan_rush_gift(
    origin: Annotated[str, "출발지 이름. 예: 강남역"],
    destination: Annotated[str, "목적지 이름. 예: 판교역"],
    relationship: Annotated[str, "받는 사람과의 관계. 예: 여자친구, 상사, 친구, 부모님"],
    occasion: Annotated[str, "상황. 예: 생일, 집들이, 사과, 감사, 기념일"],
    budget_krw: Annotated[int, "선물 예산. 원 단위."],
    minutes_until_meeting: Annotated[int, "약속까지 남은 시간. 분 단위."],
    preferences: Annotated[str, "선호 조건. 예: 디저트, 꽃, 실용적인 것"] = "",
    constraints: Annotated[str, "피해야 할 조건. 예: 향 싫어함, 술 제외"] = "",
    transport_mode: Annotated[str, "이동 수단. 예: car, taxi, transit, walk"] = "car",
    current_time: Annotated[str, "현재 시각. HH:MM 형식."] = DEFAULT_CURRENT_TIME,
    limit: Annotated[int, "반환할 추천 개수."] = 3,
) -> dict[str, object]:
    """선물 추천, 픽업 매장, 경유 가능성, 메시지를 한 번에 계획합니다."""

    return service.plan_rush_gift(
        origin=origin,
        destination=destination,
        relationship=relationship,
        occasion=occasion,
        budget_krw=budget_krw,
        minutes_until_meeting=minutes_until_meeting,
        preferences=preferences,
        constraints=constraints,
        transport_mode=transport_mode,
        current_time=current_time,
        limit=limit,
    )


@mcp.tool()
def recommend_gifts(
    relationship: Annotated[str, "받는 사람과의 관계. 예: 여자친구, 상사, 친구, 부모님"],
    occasion: Annotated[str, "상황. 예: 생일, 집들이, 사과, 감사, 기념일"],
    budget_krw: Annotated[int, "선물 예산. 원 단위."],
    preferences: Annotated[str, "선호 조건. 예: 디저트, 꽃, 실용적인 것"] = "",
    constraints: Annotated[str, "피해야 할 조건. 예: 향 싫어함, 술 제외"] = "",
    limit: Annotated[int, "반환할 후보 개수."] = 5,
) -> dict[str, object]:
    """관계, 상황, 예산, 선호 조건에 맞는 선물 후보를 추천합니다."""

    return service.recommend_gifts(
        relationship=relationship,
        occasion=occasion,
        budget_krw=budget_krw,
        preferences=preferences,
        constraints=constraints,
        limit=limit,
    )


@mcp.tool()
def find_pickup_options(
    gift_ids: Annotated[list[str], "픽업 가능성을 확인할 선물 ID 목록."],
    origin: Annotated[str, "출발지 이름. 예: 강남역"],
    destination: Annotated[str, "목적지 이름. 예: 판교역"],
    minutes_until_meeting: Annotated[int, "약속까지 남은 시간. 분 단위."],
    transport_mode: Annotated[str, "이동 수단. 예: car, taxi, transit, walk"] = "car",
    current_time: Annotated[str, "현재 시각. HH:MM 형식."] = DEFAULT_CURRENT_TIME,
    limit: Annotated[int, "반환할 픽업 후보 개수."] = 5,
) -> dict[str, object]:
    """선택한 선물 후보를 픽업할 수 있는 매장과 경유 시간을 계산합니다."""

    return service.find_pickup_options(
        gift_ids=gift_ids,
        origin=origin,
        destination=destination,
        minutes_until_meeting=minutes_until_meeting,
        transport_mode=transport_mode,
        current_time=current_time,
        limit=limit,
    )


@mcp.tool()
def draft_gift_message(
    gift_name: Annotated[str, "선물 이름. 예: 미니 꽃다발"],
    relationship: Annotated[str, "받는 사람과의 관계. 예: 여자친구, 상사, 친구, 부모님"],
    occasion: Annotated[str, "상황. 예: 생일, 집들이, 사과, 감사, 기념일"],
    tone: Annotated[str, "메시지 톤. 예: warm, polite"] = "warm",
) -> dict[str, object]:
    """선물과 상황에 맞는 짧은 카드 메시지를 작성합니다."""

    return service.draft_gift_message(
        gift_name=gift_name,
        relationship=relationship,
        occasion=occasion,
        tone=tone,
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
