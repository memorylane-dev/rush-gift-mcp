from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


RiskLevel = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class Location:
    name: str
    lat: float
    lng: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Gift:
    id: str
    name: str
    category: str
    price_krw: int
    tags: list[str]
    occasions: list[str]
    relationships: list[str]
    avoid_for: list[str]
    risk_level: RiskLevel
    message_hint: str
    # 실매장 검색(POI)에 쓰는 키워드. 예: ["꽃집"]
    store_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PickupStore:
    id: str
    name: str
    address: str
    lat: float
    lng: float
    open_until: str
    pickup_ready_minutes: int
    reliability_score: float
    available_gift_ids: list[str]

    @property
    def location(self) -> Location:
        return Location(name=self.name, lat=self.lat, lng=self.lng)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GiftCriteria:
    relationship: str
    occasion: str
    budget_krw: int
    preferences: str = ""
    constraints: str = ""


@dataclass(frozen=True)
class GiftScore:
    gift_id: str
    score: float
    reasons: list[str]
    risk_notes: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RouteEstimate:
    direct_minutes: int
    via_minutes: int
    detour_minutes: int
    travel_to_store_minutes: int
    store_to_destination_minutes: int
    pickup_wait_minutes: int
    feasible: bool
    arrival_margin_minutes: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PickupOption:
    store: PickupStore
    route: RouteEstimate
    pickup_ready_minutes: int
    stock_status: str
    route_status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "store": self.store.to_dict(),
            "route": self.route.to_dict(),
            "pickup_ready_minutes": self.pickup_ready_minutes,
            "stock_status": self.stock_status,
            "route_status": self.route_status,
        }


@dataclass(frozen=True)
class RushGiftRecommendation:
    rank: int
    gift: Gift
    score: float
    reasons: list[str]
    risks: list[str]
    pickup: PickupOption | None
    message: str
    source: str

    def to_dict(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "gift": self.gift.to_dict(),
            "score": round(self.score, 2),
            "reasons": self.reasons,
            "risks": self.risks,
            "pickup": self.pickup.to_dict() if self.pickup else None,
            "message": self.message,
            "source": self.source,
        }
