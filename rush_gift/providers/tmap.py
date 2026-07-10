from __future__ import annotations

import logging
import time

import httpx

from rush_gift.models import Location
from rush_gift.providers.base import RouteProvider


logger = logging.getLogger(__name__)

TMAP_POI_URL = "https://apis.openapi.sk.com/tmap/pois"
TMAP_CAR_ROUTE_URL = "https://apis.openapi.sk.com/tmap/routes"

DEFAULT_TIMEOUT_SECONDS = 3.0
PLACE_CACHE_TTL_SECONDS = 60 * 60
ROUTE_CACHE_TTL_SECONDS = 60 * 5  # 교통 상황이 변하므로 짧게.

_CAR_MODES = {"car", "taxi", "drive", "자동차", "택시"}


def _shared_client(timeout_seconds: float) -> httpx.Client:
    # keep-alive 연결 재사용. 요청마다 TLS 핸드셰이크를 새로 하면
    # plan_rush_gift 한 번에 수십 번의 왕복이 생겨 수십 초가 걸린다.
    return httpx.Client(timeout=timeout_seconds)


class TmapPlaceProvider:
    """장소 이름 → 좌표 변환을 TMAP POI 통합검색 API로 수행한다."""

    source_name = "tmap"

    def __init__(
        self,
        app_key: str,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        cache_ttl_seconds: float = PLACE_CACHE_TTL_SECONDS,
    ) -> None:
        self._app_key = app_key
        self._client = _shared_client(timeout_seconds)
        self._cache_ttl = cache_ttl_seconds
        self._cache: dict[str, tuple[float, Location]] = {}

    def resolve_location(self, name: str) -> Location:
        normalized = name.strip()
        if not normalized:
            raise ValueError("장소 이름이 비어 있습니다.")

        cached = self._cache.get(normalized.casefold())
        if cached and time.monotonic() - cached[0] < self._cache_ttl:
            return cached[1]

        try:
            response = self._client.get(
                TMAP_POI_URL,
                params={
                    "version": 1,
                    "searchKeyword": normalized,
                    "count": 1,
                },
                headers={"appKey": self._app_key},
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            detail = str(error)
            if isinstance(error, httpx.HTTPStatusError):
                detail = f"HTTP {error.response.status_code}: {error.response.text[:200]}"
            raise ValueError(
                f"장소 검색에 실패했습니다: {normalized} (TMAP POI API 오류: {detail})"
            ) from error

        pois = (
            response.json()
            .get("searchPoiInfo", {})
            .get("pois", {})
            .get("poi", [])
        )
        if not pois:
            raise ValueError(
                f"알 수 없는 장소입니다: {normalized}. 더 구체적인 이름으로 다시 시도하세요."
            )

        top = pois[0]
        lat = top.get("frontLat") or top.get("noorLat")
        lng = top.get("frontLon") or top.get("noorLon")
        if not lat or not lng:
            raise ValueError(f"장소 좌표를 읽지 못했습니다: {normalized}")

        location = Location(
            name=top.get("name") or normalized,
            lat=float(lat),
            lng=float(lng),
        )
        self._cache[normalized.casefold()] = (time.monotonic(), location)
        return location


class TmapRouteProvider:
    """자동차 이동 시간을 TMAP 자동차 경로 API로 계산한다.

    자동차 외 수단과 API 호출 실패 시에는 fallback provider(거리 기반
    추정)로 계산해 추천 자체가 실패하지 않게 한다.

    같은 구간을 짧은 시간 안에 반복 조회하는 경우가 많아(직행 경로,
    같은 매장을 공유하는 선물들) 결과를 5분간 캐시한다.
    """

    source_name = "tmap"

    def __init__(
        self,
        app_key: str,
        fallback: RouteProvider,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        cache_ttl_seconds: float = ROUTE_CACHE_TTL_SECONDS,
    ) -> None:
        self._app_key = app_key
        self._fallback = fallback
        self._client = _shared_client(timeout_seconds)
        self._cache_ttl = cache_ttl_seconds
        self._cache: dict[tuple[float, float, float, float], tuple[float, int]] = {}

    def travel_minutes(
        self, origin: Location, destination: Location, transport_mode: str
    ) -> int:
        if transport_mode.strip().casefold() not in _CAR_MODES:
            return self._fallback.travel_minutes(origin, destination, transport_mode)

        cache_key = (
            round(origin.lat, 5),
            round(origin.lng, 5),
            round(destination.lat, 5),
            round(destination.lng, 5),
        )
        cached = self._cache.get(cache_key)
        if cached and time.monotonic() - cached[0] < self._cache_ttl:
            return cached[1]

        try:
            response = self._client.post(
                TMAP_CAR_ROUTE_URL,
                params={"version": 1},
                json={
                    "startX": str(origin.lng),
                    "startY": str(origin.lat),
                    "endX": str(destination.lng),
                    "endY": str(destination.lat),
                    "totalValue": 2,  # 요약 정보만 (totalTime/totalDistance)
                },
                headers={"appKey": self._app_key},
            )
            response.raise_for_status()
            features = response.json().get("features", [])
            properties = features[0]["properties"] if features else {}
            if "totalTime" not in properties:
                raise ValueError("TMAP 응답에 totalTime이 없습니다.")
            duration_seconds = int(properties["totalTime"])
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as error:
            logger.warning("TMAP 경로 호출 실패, 거리 기반 추정으로 대체합니다: %s", error)
            return self._fallback.travel_minutes(origin, destination, transport_mode)

        minutes = max(1, round(duration_seconds / 60))
        self._cache[cache_key] = (time.monotonic(), minutes)
        return minutes
