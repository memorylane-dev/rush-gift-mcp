from __future__ import annotations

import os

import pytest

# main.py는 import 시점에 load_settings()로 서비스를 조립하므로,
# 테스트 모듈이 main을 import하기 전(= conftest import 시점)에 env를
# 고정해야 한다. load_dotenv는 이미 설정된 env를 덮어쓰지 않으므로
# 여기 값이 .env보다 우선한다.
os.environ["RUSH_GIFT_PLACE_PROVIDER"] = "fixture"
os.environ["RUSH_GIFT_ROUTE_PROVIDER"] = "mock"


@pytest.fixture(autouse=True)
def _force_offline_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    """테스트를 로컬 .env 설정과 격리한다.

    개발자의 .env가 tmap/kakao로 되어 있어도 테스트는 항상 네트워크가
    필요 없는 fixture/mock provider로 돌아야 한다. (개별 테스트가
    monkeypatch로 다른 값을 덮어쓰는 것은 허용된다.)
    """
    monkeypatch.setenv("RUSH_GIFT_PLACE_PROVIDER", "fixture")
    monkeypatch.setenv("RUSH_GIFT_ROUTE_PROVIDER", "mock")
