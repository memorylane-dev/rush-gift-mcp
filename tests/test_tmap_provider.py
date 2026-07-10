from __future__ import annotations

from typing import Any

from rush_gift.models import Location
from rush_gift.providers.fixture import MockRouteProvider
from rush_gift.providers.tmap import TmapRouteProvider


GANGNAM = Location(name="강남역", lat=37.498046, lng=127.027963)
PANGYO = Location(name="판교역", lat=37.395893, lng=127.111236)


class _StubResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict[str, Any]:
        return self._payload


class _CountingClient:
    def __init__(self, total_time_seconds: int) -> None:
        self.calls = 0
        self._total_time = total_time_seconds

    def post(self, *args: Any, **kwargs: Any) -> _StubResponse:
        self.calls += 1
        return _StubResponse(
            {"features": [{"properties": {"totalTime": self._total_time}}]}
        )


def _provider_with_stub(total_time_seconds: int = 1879) -> tuple[TmapRouteProvider, _CountingClient]:
    provider = TmapRouteProvider("test-key", fallback=MockRouteProvider())
    stub = _CountingClient(total_time_seconds)
    provider._client = stub  # type: ignore[assignment]
    return provider, stub


def test_route_result_is_cached() -> None:
    provider, stub = _provider_with_stub()

    first = provider.travel_minutes(GANGNAM, PANGYO, "car")
    second = provider.travel_minutes(GANGNAM, PANGYO, "car")

    assert first == second == 31  # 1879초 → 31분
    assert stub.calls == 1  # 두 번째 호출은 캐시에서


def test_reverse_direction_is_separate_cache_entry() -> None:
    provider, stub = _provider_with_stub()

    provider.travel_minutes(GANGNAM, PANGYO, "car")
    provider.travel_minutes(PANGYO, GANGNAM, "car")

    assert stub.calls == 2


def test_non_car_mode_uses_fallback_without_api_call() -> None:
    provider, stub = _provider_with_stub()

    minutes = provider.travel_minutes(GANGNAM, PANGYO, "walk")

    assert stub.calls == 0
    assert minutes >= 1  # 거리 기반 추정값
