"""TMAP API 연결 확인 스크립트.

사용법:
    1. .env 에 TMAP_APP_KEY 를 넣는다.
    2. uv run python scripts/check_tmap.py

각 API를 개별적으로 호출해서 어디까지 되는지 단계별로 보여준다.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from rush_gift.config import load_settings
from rush_gift.providers.tmap import TMAP_CAR_ROUTE_URL, TmapPlaceProvider

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
    if not settings.tmap_app_key:
        print("[실패] TMAP_APP_KEY가 비어 있습니다. .env를 확인하세요.")
        return 1
    key = settings.tmap_app_key
    print(f"[OK] TMAP_APP_KEY 감지 (길이 {len(key)}, 끝 4자리 ...{key[-4:]})")

    print("\n=== 2. TMAP POI: 장소 → 좌표 ===")
    place_provider = TmapPlaceProvider(key)
    locations = {}
    for name in (ORIGIN_NAME, DESTINATION_NAME):
        try:
            location = place_provider.resolve_location(name)
        except ValueError as error:
            print(f"[실패] {name}: {error}")
            print("  → 401/403이면 openapi.sk.com 마이페이지에서 앱 키와")
            print("    TMAP API 사용 신청 상태를 확인하세요.")
            return 1
        locations[name] = location
        print(f"[OK] {name} → {location.name} (lat={location.lat}, lng={location.lng})")

    print("\n=== 3. TMAP 자동차 경로 시간 ===")
    origin = locations[ORIGIN_NAME]
    destination = locations[DESTINATION_NAME]
    response = httpx.post(
        TMAP_CAR_ROUTE_URL,
        params={"version": 1},
        json={
            "startX": str(origin.lng),
            "startY": str(origin.lat),
            "endX": str(destination.lng),
            "endY": str(destination.lat),
            "totalValue": 2,
        },
        headers={"appKey": key},
        timeout=5.0,
    )
    if response.status_code != 200:
        print(f"[실패] HTTP {response.status_code}: {response.text[:300]}")
        return 1
    features = response.json().get("features", [])
    properties = features[0].get("properties", {}) if features else {}
    if "totalTime" not in properties:
        print(f"[실패] 응답에 totalTime 없음: {response.text[:300]}")
        return 1
    minutes = round(properties["totalTime"] / 60)
    print(f"[OK] {ORIGIN_NAME} → {DESTINATION_NAME} 자동차 약 {minutes}분")

    print("\n모든 확인 통과. .env 설정으로 서버를 띄우면 실데이터로 동작합니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
