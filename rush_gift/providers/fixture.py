from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rush_gift.models import Gift, GiftCriteria, Location, PickupStore


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load_json(filename: str) -> list[dict[str, Any]]:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as file:
        return json.load(file)


class FixtureGiftProvider:
    source_name = "fixture"

    def __init__(self, data_file: str = "gifts.json") -> None:
        self._gifts = [Gift(**item) for item in _load_json(data_file)]

    def search_gifts(self, criteria: GiftCriteria) -> list[Gift]:
        return [gift for gift in self._gifts if gift.price_krw <= criteria.budget_krw]

    def get_gifts(self, gift_ids: list[str]) -> list[Gift]:
        wanted = set(gift_ids)
        return [gift for gift in self._gifts if gift.id in wanted]


class FixturePickupStoreProvider:
    source_name = "fixture"

    def __init__(self, data_file: str = "stores.json") -> None:
        self._stores = [PickupStore(**item) for item in _load_json(data_file)]

    def find_stores(self, gift_ids: list[str]) -> list[PickupStore]:
        wanted = set(gift_ids)
        return [
            store
            for store in self._stores
            if wanted.intersection(store.available_gift_ids)
        ]


class FixturePlaceProvider:
    def __init__(self, data_file: str = "places.json") -> None:
        self._places = {
            item["name"].casefold(): Location(**item)
            for item in _load_json(data_file)
        }

    def resolve_location(self, name: str) -> Location:
        normalized = name.strip().casefold()
        if normalized in self._places:
            return self._places[normalized]

        for key, location in self._places.items():
            if normalized in key or key in normalized:
                return location

        known = ", ".join(location.name for location in self._places.values())
        raise ValueError(f"알 수 없는 장소입니다: {name}. 샘플 장소: {known}")


class MockRouteProvider:
    def travel_minutes(self, origin: Location, destination: Location, transport_mode: str) -> int:
        distance_km = _haversine_km(origin.lat, origin.lng, destination.lat, destination.lng)
        speed_kmh = _speed_for_mode(transport_mode)
        base_minutes = distance_km / speed_kmh * 60
        # Add small friction for parking, crossings, and station exits.
        return max(1, round(base_minutes + 4))


def _speed_for_mode(transport_mode: str) -> float:
    mode = transport_mode.strip().casefold()
    if mode in {"walk", "walking", "도보"}:
        return 4.2
    if mode in {"transit", "subway", "public", "대중교통", "지하철"}:
        return 22.0
    if mode in {"taxi", "car", "drive", "자동차", "택시"}:
        return 34.0
    return 28.0


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    radius_km = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    )
    return 2 * radius_km * asin(sqrt(a))
