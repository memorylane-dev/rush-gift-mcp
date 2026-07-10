from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


PLACE_PROVIDERS = ("fixture", "kakao_local", "tmap")
ROUTE_PROVIDERS = ("mock", "kakao_mobility", "tmap")
STORE_PROVIDERS = ("fixture", "tmap")

_ENV_LOADED = False


def _ensure_env_loaded() -> None:
    """Load .env once for local development.

    load_dotenv never overrides variables that are already set in the real
    environment, so platform-level settings (Vercel dashboard, Claude Desktop
    config) always win over the local .env file.
    """
    global _ENV_LOADED
    if not _ENV_LOADED:
        load_dotenv()
        _ENV_LOADED = True


@dataclass(frozen=True)
class Settings:
    place_provider: str
    route_provider: str
    kakao_rest_api_key: str | None
    tmap_app_key: str | None = None
    store_provider: str = "fixture"


def load_settings() -> Settings:
    _ensure_env_loaded()

    place_provider = _choice("RUSH_GIFT_PLACE_PROVIDER", PLACE_PROVIDERS, default="fixture")
    route_provider = _choice("RUSH_GIFT_ROUTE_PROVIDER", ROUTE_PROVIDERS, default="mock")
    store_provider = _choice("RUSH_GIFT_STORE_PROVIDER", STORE_PROVIDERS, default="fixture")
    kakao_key = os.getenv("KAKAO_REST_API_KEY", "").strip() or None
    tmap_key = os.getenv("TMAP_APP_KEY", "").strip() or None

    needs_kakao_key = place_provider == "kakao_local" or route_provider == "kakao_mobility"
    if needs_kakao_key and not kakao_key:
        raise RuntimeError(
            "KAKAO_REST_API_KEY가 설정되지 않았습니다. "
            "kakao_local/kakao_mobility provider를 쓰려면 Kakao Developers에서 "
            "발급한 REST API 키를 환경 변수로 넣어주세요. "
            "(로컬: .env 파일, Vercel: 프로젝트 Settings > Environment Variables)"
        )

    needs_tmap_key = (
        place_provider == "tmap"
        or route_provider == "tmap"
        or store_provider == "tmap"
    )
    if needs_tmap_key and not tmap_key:
        raise RuntimeError(
            "TMAP_APP_KEY가 설정되지 않았습니다. "
            "tmap provider를 쓰려면 openapi.sk.com에서 발급한 앱 키를 "
            "환경 변수로 넣어주세요. "
            "(로컬: .env 파일, Vercel: 프로젝트 Settings > Environment Variables)"
        )

    return Settings(
        place_provider=place_provider,
        route_provider=route_provider,
        kakao_rest_api_key=kakao_key,
        tmap_app_key=tmap_key,
        store_provider=store_provider,
    )


def _choice(name: str, allowed: tuple[str, ...], *, default: str) -> str:
    value = (os.getenv(name) or default).strip().casefold()
    if value not in allowed:
        raise RuntimeError(
            f"{name}={value!r} 는 지원하지 않는 값입니다. 가능한 값: {', '.join(allowed)}"
        )
    return value
