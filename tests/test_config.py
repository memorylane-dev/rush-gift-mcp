from __future__ import annotations

import pytest

from rush_gift.config import Settings, load_settings
from rush_gift.providers.fixture import FixturePlaceProvider, MockRouteProvider
from rush_gift.providers.kakao import (
    KakaoLocalPlaceProvider,
    KakaoMobilityRouteProvider,
)
from rush_gift.providers.tmap import TmapPlaceProvider, TmapRouteProvider
from rush_gift.services import create_default_service


def test_defaults_to_fixture_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RUSH_GIFT_PLACE_PROVIDER", raising=False)
    monkeypatch.delenv("RUSH_GIFT_ROUTE_PROVIDER", raising=False)

    settings = load_settings()

    assert settings.place_provider == "fixture"
    assert settings.route_provider == "mock"


def test_kakao_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUSH_GIFT_PLACE_PROVIDER", "kakao_local")
    monkeypatch.delenv("KAKAO_REST_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="KAKAO_REST_API_KEY"):
        load_settings()


def test_unknown_provider_value_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUSH_GIFT_PLACE_PROVIDER", "naver")

    with pytest.raises(RuntimeError, match="RUSH_GIFT_PLACE_PROVIDER"):
        load_settings()


def test_factory_builds_fixture_service_by_default() -> None:
    service = create_default_service(
        Settings(place_provider="fixture", route_provider="mock", kakao_rest_api_key=None)
    )

    assert isinstance(service.place_provider, FixturePlaceProvider)
    assert isinstance(service.route_provider, MockRouteProvider)


def test_factory_builds_kakao_providers_without_network() -> None:
    service = create_default_service(
        Settings(
            place_provider="kakao_local",
            route_provider="kakao_mobility",
            kakao_rest_api_key="test-key",
        )
    )

    assert isinstance(service.place_provider, KakaoLocalPlaceProvider)
    assert isinstance(service.route_provider, KakaoMobilityRouteProvider)


def test_tmap_provider_requires_app_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUSH_GIFT_PLACE_PROVIDER", "tmap")
    monkeypatch.delenv("TMAP_APP_KEY", raising=False)

    with pytest.raises(RuntimeError, match="TMAP_APP_KEY"):
        load_settings()


def test_factory_builds_tmap_providers_without_network() -> None:
    service = create_default_service(
        Settings(
            place_provider="tmap",
            route_provider="tmap",
            kakao_rest_api_key=None,
            tmap_app_key="test-key",
        )
    )

    assert isinstance(service.place_provider, TmapPlaceProvider)
    assert isinstance(service.route_provider, TmapRouteProvider)


def test_metadata_reflects_selected_providers() -> None:
    service = create_default_service(
        Settings(place_provider="fixture", route_provider="mock", kakao_rest_api_key=None)
    )

    result = service.recommend_gifts(
        relationship="친구", occasion="생일", budget_krw=30000
    )
    metadata = result["metadata"]

    assert metadata["place_source"] == "fixture"
    assert metadata["route_source"] == "mock_estimate"
    assert metadata["gift_source"] == "fixture"
