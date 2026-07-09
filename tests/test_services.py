from __future__ import annotations

from rush_gift.services import create_default_service


def test_plan_rush_gift_returns_feasible_recommendations() -> None:
    service = create_default_service()

    result = service.plan_rush_gift(
        origin="강남역",
        destination="판교역",
        relationship="여자친구",
        occasion="생일",
        budget_krw=30_000,
        minutes_until_meeting=35,
        preferences="꽃 디저트",
        limit=3,
    )

    recommendations = result["recommendations"]
    assert len(recommendations) == 3
    assert any(item["pickup"]["route"]["feasible"] for item in recommendations)
    assert recommendations[0]["gift"]["price_krw"] <= 30_000
    assert recommendations[0]["message"]
    assert result["metadata"]["gift_source"] == "fixture"


def test_plan_rush_gift_returns_fallback_when_timing_is_impossible() -> None:
    service = create_default_service()

    result = service.plan_rush_gift(
        origin="강남역",
        destination="판교역",
        relationship="친구",
        occasion="사과",
        budget_krw=20_000,
        minutes_until_meeting=5,
        limit=3,
    )

    assert result["fallback"] is not None
    assert all(
        not item["pickup"]["route"]["feasible"]
        for item in result["recommendations"]
        if item["pickup"]
    )


def test_recommend_gifts_respects_budget() -> None:
    service = create_default_service()

    result = service.recommend_gifts(
        relationship="상사",
        occasion="집들이",
        budget_krw=24_000,
        constraints="향 싫어함",
    )

    prices = [item["gift"]["price_krw"] for item in result["gifts"]]
    assert prices
    assert all(price <= 24_000 for price in prices)


def test_recommend_gifts_penalizes_contextual_avoid_rules() -> None:
    service = create_default_service()

    result = service.recommend_gifts(
        relationship="상사",
        occasion="집들이",
        budget_krw=30_000,
        limit=8,
    )

    flower = next(
        item
        for item in result["gifts"]
        if item["gift"]["id"] == "flower-mini-001"
    )
    assert flower["score"] < result["gifts"][0]["score"]
    assert any("제약 조건과 충돌" in risk for risk in flower["risks"])


def test_find_pickup_options_returns_matching_gift_ids() -> None:
    service = create_default_service()

    result = service.find_pickup_options(
        gift_ids=["flower-mini-001", "dessert-macaron-001"],
        origin="강남역",
        destination="판교역",
        minutes_until_meeting=35,
    )

    assert result["options"]
    assert all(option["gift_ids"] for option in result["options"])
    assert result["metadata"]["route_source"] == "mock_estimate"
