from __future__ import annotations

from rush_gift.config import Settings, load_settings
from rush_gift.models import (
    Gift,
    GiftCriteria,
    Location,
    PickupOption,
    PickupStore,
    RouteEstimate,
    RushGiftRecommendation,
)
from rush_gift.providers.base import (
    GiftProvider,
    PickupStoreProvider,
    PlaceProvider,
    RouteProvider,
)
from rush_gift.providers.fixture import (
    FixtureGiftProvider,
    FixturePickupStoreProvider,
    FixturePlaceProvider,
    MockRouteProvider,
)
from rush_gift.scoring import score_gift, score_pickup_option


DEFAULT_CURRENT_TIME = "18:00"
STOP_HANDOFF_MINUTES = 3
# 경로 계산은 외부 API 호출이라 비싸다. 거리 기반 추정으로 매장을
# 선별한 뒤 이 개수만큼만 실제 경로를 계산한다.
ROUTE_CHECK_STORES_PER_GIFT = 1
ROUTE_CHECK_STORES_MAX = 5

# 매장 선별용 추정기. 실제 경로 provider와 무관하게 항상 무료다.
_ROUTE_ESTIMATOR = MockRouteProvider()


class RushGiftService:
    def __init__(
        self,
        gift_provider: GiftProvider,
        pickup_store_provider: PickupStoreProvider,
        place_provider: PlaceProvider,
        route_provider: RouteProvider,
    ) -> None:
        self.gift_provider = gift_provider
        self.pickup_store_provider = pickup_store_provider
        self.place_provider = place_provider
        self.route_provider = route_provider

    def plan_rush_gift(
        self,
        *,
        origin: str,
        destination: str,
        relationship: str,
        occasion: str,
        budget_krw: int,
        minutes_until_meeting: int,
        preferences: str = "",
        constraints: str = "",
        transport_mode: str = "car",
        current_time: str = DEFAULT_CURRENT_TIME,
        limit: int = 3,
    ) -> dict[str, object]:
        criteria = GiftCriteria(
            relationship=relationship,
            occasion=occasion,
            budget_krw=budget_krw,
            preferences=preferences,
            constraints=constraints,
        )
        origin_location = self.place_provider.resolve_location(origin)
        destination_location = self.place_provider.resolve_location(destination)
        gift_scores = self._rank_gifts(criteria)
        recommendations: list[RushGiftRecommendation] = []

        # 경로 계산은 외부 API 호출이라 비싸다. 상위 후보만 검토한다.
        candidate_count = min(8, max(4, limit * 2))
        for gift, base_score, reasons, risks in gift_scores[:candidate_count]:
            pickup = self._best_pickup_option(
                gift=gift,
                origin=origin_location,
                destination=destination_location,
                minutes_until_meeting=minutes_until_meeting,
                transport_mode=transport_mode,
                current_time=current_time,
            )
            pickup_score = score_pickup_option(pickup) if pickup else -20
            final_score = base_score + pickup_score
            if pickup and pickup.route.feasible:
                reasons = [*reasons, "약속 시간 안에 픽업 후 도착할 수 있습니다."]
            elif pickup:
                risks = [*risks, "약속 시간 안에 픽업하기 어렵습니다."]
            else:
                risks = [*risks, "픽업 가능한 샘플 매장을 찾지 못했습니다."]

            recommendations.append(
                RushGiftRecommendation(
                    rank=0,
                    gift=gift,
                    score=final_score,
                    reasons=reasons[:6],
                    risks=risks[:4],
                    pickup=pickup,
                    message=self.draft_gift_message(
                        gift_name=gift.name,
                        relationship=relationship,
                        occasion=occasion,
                    )["message"],
                    source=_source_of(self.gift_provider),
                )
            )

        ranked = sorted(recommendations, key=lambda item: item.score, reverse=True)[:limit]
        ranked = [
            RushGiftRecommendation(
                rank=index,
                gift=item.gift,
                score=item.score,
                reasons=item.reasons,
                risks=item.risks,
                pickup=item.pickup,
                message=item.message,
                source=item.source,
            )
            for index, item in enumerate(ranked, start=1)
        ]

        feasible_count = sum(1 for item in ranked if item.pickup and item.pickup.route.feasible)
        return {
            "summary": _summary_for_plan(feasible_count),
            "input": {
                "origin": origin_location.to_dict(),
                "destination": destination_location.to_dict(),
                "relationship": relationship,
                "occasion": occasion,
                "budget_krw": budget_krw,
                "minutes_until_meeting": minutes_until_meeting,
                "transport_mode": transport_mode,
                "current_time": current_time,
            },
            "recommendations": [item.to_dict() for item in ranked],
            "fallback": _fallback_for_timing(feasible_count),
            "metadata": self._metadata(),
        }

    def recommend_gifts(
        self,
        *,
        relationship: str,
        occasion: str,
        budget_krw: int,
        preferences: str = "",
        constraints: str = "",
        limit: int = 5,
    ) -> dict[str, object]:
        criteria = GiftCriteria(
            relationship=relationship,
            occasion=occasion,
            budget_krw=budget_krw,
            preferences=preferences,
            constraints=constraints,
        )
        ranked = self._rank_gifts(criteria)[:limit]
        return {
            "summary": f"{len(ranked)}개의 선물 후보를 찾았습니다.",
            "gifts": [
                {
                    "gift": gift.to_dict(),
                    "score": round(score, 2),
                    "reasons": reasons,
                    "risks": risks,
                }
                for gift, score, reasons, risks in ranked
            ],
            "metadata": self._metadata(),
        }

    def find_pickup_options(
        self,
        *,
        gift_ids: list[str],
        origin: str,
        destination: str,
        minutes_until_meeting: int,
        transport_mode: str = "car",
        current_time: str = DEFAULT_CURRENT_TIME,
        limit: int = 5,
    ) -> dict[str, object]:
        origin_location = self.place_provider.resolve_location(origin)
        destination_location = self.place_provider.resolve_location(destination)
        stores = [
            store
            for store in self.pickup_store_provider.find_stores(
                gift_ids, near=destination_location
            )
            if _is_open_at(store, current_time)
        ]
        stores = self._top_stores_by_estimate(
            stores,
            origin=origin_location,
            destination=destination_location,
            minutes_until_meeting=minutes_until_meeting,
            transport_mode=transport_mode,
            count=max(limit, ROUTE_CHECK_STORES_MAX),
        )
        options: list[dict[str, object]] = []
        for store in stores:
            matching_gift_ids = sorted(set(gift_ids).intersection(store.available_gift_ids))
            route = self._route_via_store(
                origin=origin_location,
                destination=destination_location,
                store=store,
                minutes_until_meeting=minutes_until_meeting,
                transport_mode=transport_mode,
            )
            option = PickupOption(
                store=store,
                route=route,
                pickup_ready_minutes=store.pickup_ready_minutes,
                stock_status=self._stock_status(),
                route_status="estimated",
            )
            options.append(
                {
                    "gift_ids": matching_gift_ids,
                    "score": round(score_pickup_option(option), 2),
                    "option": option.to_dict(),
                }
            )

        options = sorted(options, key=lambda item: item["score"], reverse=True)[:limit]
        return {
            "summary": f"{len(options)}개의 픽업 후보를 찾았습니다.",
            "options": options,
            "metadata": self._metadata(),
        }

    def draft_gift_message(
        self,
        *,
        gift_name: str,
        relationship: str,
        occasion: str,
        tone: str = "warm",
    ) -> dict[str, object]:
        message = _draft_message(
            gift_name=gift_name,
            relationship=relationship,
            occasion=occasion,
            tone=tone,
        )
        return {
            "message": message,
            "metadata": {
                "source": "template",
                "note": "MVP uses deterministic message templates.",
            },
        }

    def _metadata(self) -> dict[str, object]:
        return {
            "gift_source": _source_of(self.gift_provider),
            "store_source": _source_of(self.pickup_store_provider),
            "place_source": _source_of(self.place_provider),
            "route_source": _source_of(self.route_provider),
            "stock_status": self._stock_status(),
            "route_status": "estimated",
            "privacy": "request data is not persisted",
        }

    def _stock_status(self) -> str:
        # fixture 매장은 시뮬레이션 값, 실매장은 재고를 알 수 없음을 명시.
        if _source_of(self.pickup_store_provider) == "fixture":
            return "simulated"
        return "unknown"

    def _rank_gifts(
        self,
        criteria: GiftCriteria,
    ) -> list[tuple[Gift, float, list[str], list[str]]]:
        gifts = self.gift_provider.search_gifts(criteria)
        scored = []
        for gift in gifts:
            gift_score = score_gift(gift, criteria)
            scored.append((gift, gift_score.score, gift_score.reasons, gift_score.risk_notes))
        return sorted(scored, key=lambda item: item[1], reverse=True)

    def _best_pickup_option(
        self,
        *,
        gift: Gift,
        origin: Location,
        destination: Location,
        minutes_until_meeting: int,
        transport_mode: str,
        current_time: str,
    ) -> PickupOption | None:
        stores = [
            store
            for store in self.pickup_store_provider.find_stores(
                [gift.id], near=destination
            )
            if _is_open_at(store, current_time)
        ]
        stores = self._top_stores_by_estimate(
            stores,
            origin=origin,
            destination=destination,
            minutes_until_meeting=minutes_until_meeting,
            transport_mode=transport_mode,
            count=ROUTE_CHECK_STORES_PER_GIFT,
        )
        options = [
            PickupOption(
                store=store,
                route=self._route_via_store(
                    origin=origin,
                    destination=destination,
                    store=store,
                    minutes_until_meeting=minutes_until_meeting,
                    transport_mode=transport_mode,
                ),
                pickup_ready_minutes=store.pickup_ready_minutes,
                stock_status=self._stock_status(),
                route_status="estimated",
            )
            for store in stores
        ]
        if not options:
            return None
        return max(options, key=score_pickup_option)

    def _top_stores_by_estimate(
        self,
        stores: list[PickupStore],
        *,
        origin: Location,
        destination: Location,
        minutes_until_meeting: int,
        transport_mode: str,
        count: int,
    ) -> list[PickupStore]:
        """점수가 높을 것으로 추정되는 매장만 남긴다.

        실제 경로 API 대신 거리 기반 추정으로 점수를 매기므로 외부
        호출 없이 후보를 좁힐 수 있다. 최종 응답에 나가는 경로 수치는
        이후 실제 route_provider로 다시 계산된다.
        """
        if len(stores) <= count:
            return stores
        scored = []
        for store in stores:
            option = PickupOption(
                store=store,
                route=self._route_via_store(
                    origin=origin,
                    destination=destination,
                    store=store,
                    minutes_until_meeting=minutes_until_meeting,
                    transport_mode=transport_mode,
                    route_provider=_ROUTE_ESTIMATOR,
                ),
                pickup_ready_minutes=store.pickup_ready_minutes,
                stock_status="estimate",
                route_status="estimate",
            )
            scored.append((score_pickup_option(option), store))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [store for _, store in scored[:count]]

    def _route_via_store(
        self,
        *,
        origin: Location,
        destination: Location,
        store: PickupStore,
        minutes_until_meeting: int,
        transport_mode: str,
        route_provider: RouteProvider | None = None,
    ) -> RouteEstimate:
        provider = route_provider or self.route_provider
        direct = provider.travel_minutes(origin, destination, transport_mode)
        to_store = provider.travel_minutes(origin, store.location, transport_mode)
        store_to_dest = provider.travel_minutes(store.location, destination, transport_mode)
        pickup_wait = max(0, store.pickup_ready_minutes - to_store)
        via = to_store + pickup_wait + STOP_HANDOFF_MINUTES + store_to_dest
        margin = minutes_until_meeting - via
        return RouteEstimate(
            direct_minutes=direct,
            via_minutes=via,
            detour_minutes=via - direct,
            travel_to_store_minutes=to_store,
            store_to_destination_minutes=store_to_dest,
            pickup_wait_minutes=pickup_wait,
            feasible=margin >= 0,
            arrival_margin_minutes=margin,
        )


def create_default_service(settings: Settings | None = None) -> RushGiftService:
    """환경 변수 설정에 따라 provider를 조립한다.

    RUSH_GIFT_PLACE_PROVIDER / RUSH_GIFT_ROUTE_PROVIDER 값으로 fixture와
    Kakao API 구현을 선택한다. 기본값은 네트워크가 필요 없는 fixture/mock.
    """
    settings = settings or load_settings()

    gift_provider = FixtureGiftProvider()
    place_provider: PlaceProvider = FixturePlaceProvider()
    route_provider: RouteProvider = MockRouteProvider()
    pickup_store_provider: PickupStoreProvider = FixturePickupStoreProvider()

    if settings.place_provider == "kakao_local":
        from rush_gift.providers.kakao import KakaoLocalPlaceProvider

        assert settings.kakao_rest_api_key is not None  # load_settings가 보장
        place_provider = KakaoLocalPlaceProvider(settings.kakao_rest_api_key)
    elif settings.place_provider == "tmap":
        from rush_gift.providers.tmap import TmapPlaceProvider

        assert settings.tmap_app_key is not None
        place_provider = TmapPlaceProvider(settings.tmap_app_key)

    if settings.route_provider == "kakao_mobility":
        from rush_gift.providers.kakao import KakaoMobilityRouteProvider

        assert settings.kakao_rest_api_key is not None
        route_provider = KakaoMobilityRouteProvider(
            settings.kakao_rest_api_key,
            fallback=MockRouteProvider(),
        )
    elif settings.route_provider == "tmap":
        from rush_gift.providers.tmap import TmapRouteProvider

        assert settings.tmap_app_key is not None
        route_provider = TmapRouteProvider(
            settings.tmap_app_key,
            fallback=MockRouteProvider(),
        )

    if settings.store_provider == "tmap":
        from rush_gift.providers.tmap import TmapPickupStoreProvider

        assert settings.tmap_app_key is not None
        pickup_store_provider = TmapPickupStoreProvider(
            settings.tmap_app_key,
            gift_provider,
        )

    return RushGiftService(
        gift_provider=gift_provider,
        pickup_store_provider=pickup_store_provider,
        place_provider=place_provider,
        route_provider=route_provider,
    )


def _source_of(provider: object) -> str:
    return getattr(provider, "source_name", "unknown")




def _summary_for_plan(feasible_count: int) -> str:
    if feasible_count:
        return f"픽업 후 도착 가능한 추천 {feasible_count}개를 찾았습니다."
    return "약속 시간 안에 픽업 가능한 후보가 없습니다. 대체안을 확인하세요."


def _fallback_for_timing(feasible_count: int) -> dict[str, object] | None:
    if feasible_count:
        return None
    return {
        "title": "픽업 시간이 부족합니다.",
        "suggestions": [
            "목적지 근처에서 바로 받을 수 있는 후보만 다시 검색하세요.",
            "실물 선물 대신 짧은 메시지와 모바일 교환권을 먼저 보내세요.",
            "도착 후 함께 고르는 방식으로 약속을 전환하세요.",
        ],
    }




def _is_open_at(store: PickupStore, current_time: str) -> bool:
    return _minutes(current_time) <= _minutes(store.open_until)


def _minutes(value: str) -> int:
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)


def _draft_message(gift_name: str, relationship: str, occasion: str, tone: str) -> str:
    context = f"{relationship} {occasion}".casefold()
    if "상사" in context or "manager" in context:
        return f"작지만 감사한 마음으로 {gift_name} 준비했습니다. 편하게 받아주세요."
    if "사과" in context or "apology" in context:
        return f"말로 다 못 전한 마음을 담아 {gift_name} 준비했어. 미안하고 고마워."
    if "부모" in context or "parents" in context:
        return f"생각나서 {gift_name} 챙겨가요. 같이 드시면 좋겠어요."
    if "생일" in context or "birthday" in context:
        return f"급하게 준비했지만 오늘 생각하면서 {gift_name} 골랐어. 생일 축하해."
    if tone == "polite":
        return f"작은 마음으로 {gift_name} 준비했습니다. 받아주시면 감사하겠습니다."
    return f"생각나서 {gift_name} 준비했어. 오늘 만나서 전해줄게."
