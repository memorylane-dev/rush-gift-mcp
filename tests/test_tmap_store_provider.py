from __future__ import annotations

from typing import Any

from rush_gift.models import Location
from rush_gift.providers.fixture import FixtureGiftProvider
from rush_gift.providers.tmap import TmapPickupStoreProvider


PANGYO = Location(name="판교역", lat=37.395893, lng=127.111236)

_POI_PAYLOAD = {
    "searchPoiInfo": {
        "pois": {
            "poi": [
                {
                    "id": "1001",
                    "name": "판교꽃집",
                    "upperAddrName": "경기",
                    "middleAddrName": "성남시 분당구",
                    "roadName": "판교역로",
                    "firstBuildingNo": "1",
                    "frontLat": "37.3960",
                    "frontLon": "127.1110",
                }
            ]
        }
    }
}


class _StubResponse:
    status_code = 200
    content = b"{}"

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict[str, Any]:
        return self._payload


class _CountingClient:
    def __init__(self) -> None:
        self.calls = 0

    def get(self, *args: Any, **kwargs: Any) -> _StubResponse:
        self.calls += 1
        return _StubResponse(_POI_PAYLOAD)


def _provider_with_stub() -> tuple[TmapPickupStoreProvider, _CountingClient]:
    provider = TmapPickupStoreProvider("test-key", FixtureGiftProvider())
    stub = _CountingClient()
    provider._client = stub  # type: ignore[assignment]
    return provider, stub


def test_finds_real_stores_by_gift_keyword() -> None:
    provider, stub = _provider_with_stub()

    stores = provider.find_stores(["flower-mini-001"], near=PANGYO)

    assert stub.calls == 1
    assert len(stores) == 1
    store = stores[0]
    assert store.id == "tmap-1001"
    assert store.name == "판교꽃집"
    assert store.available_gift_ids == ["flower-mini-001"]
    assert "경기" in store.address


def test_returns_empty_without_center_location() -> None:
    provider, stub = _provider_with_stub()

    assert provider.find_stores(["flower-mini-001"]) == []
    assert stub.calls == 0


def test_keyword_search_is_cached() -> None:
    provider, stub = _provider_with_stub()

    provider.find_stores(["flower-mini-001"], near=PANGYO)
    provider.find_stores(["flower-mini-001"], near=PANGYO)

    assert stub.calls == 1
