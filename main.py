from __future__ import annotations

import os
from typing import Annotated, Literal, cast

from pydantic import Field

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse

from rush_gift.config import load_settings
from rush_gift.services import DEFAULT_CURRENT_TIME, create_default_service


Transport = Literal["stdio", "sse", "streamable-http"]
APP_NAME = "오다 주웠다"
DEFAULT_HTTP_PATH = "/mcp"


def _normalize_transport(value: str | None) -> Transport:
    normalized = (value or "stdio").strip().casefold().replace("_", "-")
    if normalized == "http":
        normalized = "streamable-http"
    if normalized not in {"stdio", "sse", "streamable-http"}:
        raise ValueError(
            "MCP_TRANSPORT must be one of: stdio, sse, streamable-http, http"
        )
    return cast(Transport, normalized)


def _env_int(*names: str, default: int) -> int:
    for name in names:
        value = os.getenv(name)
        if value:
            return int(value)
    return default


def _env_bool(*names: str, default: bool = False) -> bool:
    for name in names:
        value = os.getenv(name)
        if value:
            return value.strip().casefold() in {"1", "true", "yes", "on"}
    return default


def _http_path() -> str:
    path = (
        os.getenv("FASTMCP_STREAMABLE_HTTP_PATH")
        or os.getenv("MCP_HTTP_PATH")
        or DEFAULT_HTTP_PATH
    )
    return path if path.startswith("/") else f"/{path}"


TRANSPORT = _normalize_transport(os.getenv("MCP_TRANSPORT"))
HTTP_HOST = (
    os.getenv("FASTMCP_HOST")
    or os.getenv("HOST")
    or ("0.0.0.0" if TRANSPORT == "streamable-http" else "127.0.0.1")
)
HTTP_PORT = _env_int("FASTMCP_PORT", "PORT", default=8000)
HTTP_PATH = _http_path()
STATELESS_HTTP = _env_bool(
    "FASTMCP_STATELESS_HTTP",
    "MCP_STATELESS_HTTP",
    default=bool(os.getenv("VERCEL")),
)


settings = load_settings()


def _instructions() -> str:
    if settings.place_provider == "fixture":
        data_note = "모든 MVP 데이터는 fixture이며 "
    else:
        data_note = (
            "장소 좌표와 이동 시간은 실시간 API 기반이고, "
            "선물/매장 데이터는 샘플이며 "
        )
    return (
        "약속 장소로 가는 길에 급하게 선물이 필요한 사용자에게 지금 픽업 가능한 "
        "선물, 경유 시간, 실패 리스크, 짧은 선물 메시지를 추천합니다. "
        f"{data_note}실시간 재고/결제/예약을 보장하지 않습니다."
    )


mcp = FastMCP(
    APP_NAME,
    instructions=_instructions(),
    host=HTTP_HOST,
    port=HTTP_PORT,
    streamable_http_path=HTTP_PATH,
    stateless_http=STATELESS_HTTP,
)
service = create_default_service(settings)


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health_check(_request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "name": APP_NAME,
            "mcp_path": HTTP_PATH,
            "transport": TRANSPORT,
            "stateless_http": STATELESS_HTTP,
            # Vercel이 git 연동 배포 시 자동 주입. 로컬에서는 "local".
            "commit": os.getenv("VERCEL_GIT_COMMIT_SHA", "local")[:7],
            "place_provider": settings.place_provider,
            "route_provider": settings.route_provider,
        }
    )


@mcp.tool(
    annotations=ToolAnnotations(
        title="Plan a rush gift pickup",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,  # 외부 지도/경로 API 호출
    )
)
def plan_rush_gift(
    origin: Annotated[str, Field(description="출발지 이름. 예: 강남역")],
    destination: Annotated[str, Field(description="목적지 이름. 예: 판교역")],
    relationship: Annotated[str, Field(description="받는 사람과의 관계. 예: 여자친구, 상사, 친구, 부모님")],
    occasion: Annotated[str, Field(description="상황. 예: 생일, 집들이, 사과, 감사, 기념일")],
    budget_krw: Annotated[int, Field(description="선물 예산. 원 단위.")],
    minutes_until_meeting: Annotated[int, Field(description="약속까지 남은 시간. 분 단위.")],
    preferences: Annotated[str, Field(description="선호 조건. 예: 디저트, 꽃, 실용적인 것")] = "",
    constraints: Annotated[str, Field(description="피해야 할 조건. 예: 향 싫어함, 술 제외")] = "",
    transport_mode: Annotated[str, Field(description="이동 수단. 예: car, taxi, transit, walk")] = "car",
    current_time: Annotated[str, Field(description="현재 시각. HH:MM 형식.")] = DEFAULT_CURRENT_TIME,
    limit: Annotated[int, Field(description="반환할 추천 개수.")] = 3,
) -> dict[str, object]:
    """Plans a last-minute gift pickup with Oda Juwotda(오다 주웠다).

    Use this tool whenever the user gives an origin, a destination, and the
    minutes left before a meeting. It returns everything in one call: gift
    recommendations, pickup stores near the destination, detour travel time,
    whether the user can still arrive on time, and a short gift message.
    If the user mentions a route or a meeting time, call this tool instead
    of recommend_gifts.
    """

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


@mcp.tool(
    annotations=ToolAnnotations(
        title="Recommend gift candidates",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
)
def recommend_gifts(
    relationship: Annotated[str, Field(description="받는 사람과의 관계. 예: 여자친구, 상사, 친구, 부모님")],
    occasion: Annotated[str, Field(description="상황. 예: 생일, 집들이, 사과, 감사, 기념일")],
    budget_krw: Annotated[int, Field(description="선물 예산. 원 단위.")],
    preferences: Annotated[str, Field(description="선호 조건. 예: 디저트, 꽃, 실용적인 것")] = "",
    constraints: Annotated[str, Field(description="피해야 할 조건. 예: 향 싫어함, 술 제외")] = "",
    limit: Annotated[int, Field(description="반환할 후보 개수.")] = 5,
) -> dict[str, object]:
    """Recommends gift ideas with Oda Juwotda(오다 주웠다) — ideas only.

    Returns gift candidates matched to relationship, occasion, budget,
    preferences, and constraints. It does not compute pickup stores or
    travel time. If origin, destination, or remaining minutes are
    available, call plan_rush_gift instead of this tool.
    """

    return service.recommend_gifts(
        relationship=relationship,
        occasion=occasion,
        budget_krw=budget_krw,
        preferences=preferences,
        constraints=constraints,
        limit=limit,
    )


@mcp.tool(
    annotations=ToolAnnotations(
        title="Find pickup stores for chosen gifts",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,  # 외부 지도/경로 API 호출
    )
)
def find_pickup_options(
    gift_ids: Annotated[list[str], Field(description="픽업 가능성을 확인할 선물 ID 목록.")],
    origin: Annotated[str, Field(description="출발지 이름. 예: 강남역")],
    destination: Annotated[str, Field(description="목적지 이름. 예: 판교역")],
    minutes_until_meeting: Annotated[int, Field(description="약속까지 남은 시간. 분 단위.")],
    transport_mode: Annotated[str, Field(description="이동 수단. 예: car, taxi, transit, walk")] = "car",
    current_time: Annotated[str, Field(description="현재 시각. HH:MM 형식.")] = DEFAULT_CURRENT_TIME,
    limit: Annotated[int, Field(description="반환할 픽업 후보 개수.")] = 5,
) -> dict[str, object]:
    """Finds pickup stores and detour times with Oda Juwotda(오다 주웠다)
    for gifts that are already chosen (gift_ids).

    Use this as a follow-up after narrowing candidates with
    recommend_gifts. When origin, destination, and remaining time are all
    known from the start, plan_rush_gift alone is enough.
    """

    return service.find_pickup_options(
        gift_ids=gift_ids,
        origin=origin,
        destination=destination,
        minutes_until_meeting=minutes_until_meeting,
        transport_mode=transport_mode,
        current_time=current_time,
        limit=limit,
    )


@mcp.tool(
    annotations=ToolAnnotations(
        title="Draft a gift card message",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
)
def draft_gift_message(
    gift_name: Annotated[str, Field(description="선물 이름. 예: 미니 꽃다발")],
    relationship: Annotated[str, Field(description="받는 사람과의 관계. 예: 여자친구, 상사, 친구, 부모님")],
    occasion: Annotated[str, Field(description="상황. 예: 생일, 집들이, 사과, 감사, 기념일")],
    tone: Annotated[str, Field(description="메시지 톤. 예: warm, polite")] = "warm",
) -> dict[str, object]:
    """Drafts a short gift card message with Oda Juwotda(오다 주웠다)
    that fits the gift, relationship, occasion, and tone."""

    return service.draft_gift_message(
        gift_name=gift_name,
        relationship=relationship,
        occasion=occasion,
        tone=tone,
    )


app = mcp.streamable_http_app()


def main() -> None:
    mcp.run(transport=TRANSPORT)


if __name__ == "__main__":
    main()
