"""Kakao API 연결 확인 스크립트.

사용법:
    1. .env 에 KAKAO_REST_API_KEY 와 provider 설정을 넣는다.
    2. uv run python scripts/check_kakao.py

각 API를 개별적으로 호출해서 어디까지 되는지 단계별로 보여준다.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from rush_gift.config import load_settings
from rush_gift.providers.kakao import (
    KAKAO_MOBILITY_DIRECTIONS_URL,
    KakaoLocalPlaceProvider,
)

ORIGIN_NAME = "강남역"
DESTINATION_NAME = "판교역"


def main() -> int:
    print("=== 1. 환경 변수 로드 ===")
    try:
        settings = load_settings()
    except RuntimeError as error:
        print(f"[실패] {error}")
        return 1
    print(f"[OK] place_provider={settings.place_provider}")
    print(f"[OK] route_provider={settings.route_provider}")
    if not settings.kakao_rest_api_key:
        print("[실패] KAKAO_REST_API_KEY가 비어 있습니다. .env를 확인하세요.")
        return 1
    key = settings.kakao_rest_api_key
    print(f"[OK] KAKAO_REST_API_KEY 감지 (길이 {len(key)}, 끝 4자리 ...{key[-4:]})")

    print("\n=== 2. Kakao Local: 장소 → 좌표 ===")
    place_provider = KakaoLocalPlaceProvider(key)
    locations = {}
    for name in (ORIGIN_NAME, DESTINATION_NAME):
        try:
            location = place_provider.resolve_location(name)
        except ValueError as error:
            print(f"[실패] {name}: {error}")
            print("  → 401이면 키가 잘못됐거나 'KakaoAK ' 접두어를 키에 포함했는지 확인.")
            print("  → 403이면 Kakao Developers 앱에서 카카오맵(Local) 사용 설정 확인.")
            return 1
        locations[name] = location
        print(f"[OK] {name} → {location.name} (lat={location.lat}, lng={location.lng})")

    print("\n=== 3. Kakao Mobility: 자동차 경로 시간 ===")
    origin = locations[ORIGIN_NAME]
    destination = locations[DESTINATION_NAME]
    response = httpx.get(
        KAKAO_MOBILITY_DIRECTIONS_URL,
        params={
            "origin": f"{origin.lng},{origin.lat}",
            "destination": f"{destination.lng},{destination.lat}",
        },
        headers={"Authorization": f"KakaoAK {key}"},
        timeout=5.0,
    )
    if response.status_code != 200:
        print(f"[실패] HTTP {response.status_code}: {response.text[:300]}")
        print("  → 401/403이면 developers.kakaomobility.com 에서 길찾기 API 이용 신청이")
        print("    되어 있는지, 카카오디벨로퍼스 앱과 연동됐는지 확인하세요.")
        print("  → Mobility가 아직 안 되어도 서버는 거리 기반 추정으로 자동 fallback 하므로")
        print("    RUSH_GIFT_ROUTE_PROVIDER=mock 으로 두고 Local만 먼저 써도 됩니다.")
        return 1
    routes = response.json().get("routes", [])
    if not routes or "summary" not in routes[0]:
        print(f"[실패] 경로 없음: {response.text[:300]}")
        return 1
    minutes = round(routes[0]["summary"]["duration"] / 60)
    print(f"[OK] {ORIGIN_NAME} → {DESTINATION_NAME} 자동차 약 {minutes}분")

    print("\n모든 확인 통과. .env 설정으로 서버를 띄우면 실데이터로 동작합니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
