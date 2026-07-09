from __future__ import annotations

from typing import Protocol

from rush_gift.models import Gift, GiftCriteria, Location, PickupStore


class GiftProvider(Protocol):
    def search_gifts(self, criteria: GiftCriteria) -> list[Gift]:
        """Return gift candidates for the criteria."""


class PickupStoreProvider(Protocol):
    def find_stores(self, gift_ids: list[str]) -> list[PickupStore]:
        """Return pickup stores that can provide at least one requested gift."""


class PlaceProvider(Protocol):
    def resolve_location(self, name: str) -> Location:
        """Resolve a place name into coordinates."""


class RouteProvider(Protocol):
    def travel_minutes(self, origin: Location, destination: Location, transport_mode: str) -> int:
        """Estimate travel time between two locations."""
