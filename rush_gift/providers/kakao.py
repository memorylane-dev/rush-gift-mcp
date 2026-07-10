from __future__ import annotations

import logging
import time

import httpx

from rush_gift.models import Location
from rush_gift.providers.base import RouteProvider


logger = logging.getLogger(__name__)

KAKAO_LOCAL_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
KAKAO_MOBILITY_DIRECTIONS_URL = "https://apis-navi.kakaomobility.com/v1/directions"

DEFAULT_TIMEOUT_SECONDS = 3.0
PLACE_CACHE_TTL_SECONDS = 60 * 60  # 장소 좌표는 사실상 불변이라 길게 캐시해도 안전.

# Kakao Mobility Directions는 자동차 경로만 제공한다.
_CAR_MODES = {"car", "taxi", "drive", "자동차", "택시"}


class KakaoLocalPlaceProvider:
    """장소 이름 → 좌표 변환을 Kakao Local 키워드 검색 API로 수행한다."""

    source_name = "kakao_local"

    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        cache_ttl_seconds: float = PLACE_CACHE_TTL_SECONDS,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout_seconds
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
            response = httpx.get(
                KAKAO_LOCAL_KEYWORD_URL,
                params={"query": normalized, "size": 1},
                headers=self._headers(),
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            detail = str(error)
            if isinstance(error, httpx.HTTPStatusError):
                detail = f"HTTP {error.response.status_code}: {error.response.text[:200]}"
            raise ValueError(
                f"장소 검색에 실패했습니다: {normalized} (Kakao Local API 오류: {detail})"
            ) from error

        documents = response.json().get("documents", [])
        if not documents:
            raise ValueError(
                f"알 수 없는 장소입니다: {normalized}. 더 구체적인 이름으로 다시 시도하세요."
            )

        top = documents[0]
        location = Location(
            name=top.get("place_name") or normalized,
            lat=float(top["y"]),
            lng=float(top["x"]),
        )
        self._cache[normalized.casefold()] = (time.monotonic(), location)
        return location

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"KakaoAK {self._api_key}"}


class KakaoMobilityRouteProvider:
    """자동차 이동 시간을 Kakao Mobility 길찾기 API로 계산한다.

    자동차 외 수단(도보/대중교통)은 API가 지원하지 않으므로 fallback
    provider(거리 기반 추정)로 계산한다. API 호출 실패 시에도 fallback을
    사용해 추천 자체가 실패하지 않게 한다.
    """

    source_name = "kakao_mobility"

    def __init__(
        self,
        api_key: str,
        fallback: RouteProvider,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key
        self._fallback = fallback
        self._timeout = timeout_seconds

    def travel_minutes(
        self, origin: Location, destination: Location, transport_mode: str
    ) -> int:
        if transport_mode.strip().casefold() not in _CAR_MODES:
            return self._fallback.travel_minutes(origin, destination, transport_mode)

        try:
            response = httpx.get(
                KAKAO_MOBILITY_DIRECTIONS_URL,
                params={
                    "origin": f"{origin.lng},{origin.lat}",
                    "destination": f"{destination.lng},{destination.lat}",
                },
                headers={"Authorization": f"KakaoAK {self._api_key}"},
                timeout=self._timeout,
            )
            response.raise_for_status()
            routes = response.json().get("routes", [])
            summary = routes[0]["summary"] if routes else None
            if not summary or "duration" not in summary:
                raise ValueError("Kakao Mobility 응답에 경로가 없습니다.")
            duration_seconds = int(summary["duration"])
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as error:
            logger.warning(
                "Kakao Mobility 호출 실패, 거리 기반 추정으로 대체합니다: %s", error
            )
            return self._fallback.travel_minutes(origin, destination, transport_mode)

        return max(1, round(duration_seconds / 60))
