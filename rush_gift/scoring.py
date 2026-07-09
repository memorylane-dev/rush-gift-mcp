from __future__ import annotations

import re

from rush_gift.models import Gift, GiftCriteria, GiftScore, PickupOption


RELATIONSHIP_ALIASES = {
    "여자친구": "girlfriend",
    "남자친구": "boyfriend",
    "애인": "partner",
    "연인": "partner",
    "친구": "friend",
    "상사": "manager",
    "팀장": "manager",
    "동료": "coworker",
    "부모님": "parents",
    "부모": "parents",
    "가족": "family",
}

OCCASION_ALIASES = {
    "생일": "birthday",
    "기념일": "anniversary",
    "집들이": "housewarming",
    "사과": "apology",
    "감사": "thanks",
    "방문": "casual_visit",
    "부모님 방문": "parents_visit",
    "데이트": "date",
}

CONSTRAINT_ALIASES = {
    "향 싫": "strong_scent_sensitive",
    "향 제외": "strong_scent_sensitive",
    "술 제외": "non_alcohol_required",
    "술 싫": "non_alcohol_required",
    "저예산": "low_budget",
}


def normalize_relationship(value: str) -> str:
    return _normalize(value, RELATIONSHIP_ALIASES)


def normalize_occasion(value: str) -> str:
    normalized = _normalize(value, OCCASION_ALIASES)
    if normalized == "casual_visit" and "부모" in value:
        return "parents_visit"
    return normalized


def normalize_constraints(value: str) -> list[str]:
    normalized: list[str] = []
    folded = value.casefold()
    for needle, replacement in CONSTRAINT_ALIASES.items():
        if needle.casefold() in folded:
            normalized.append(replacement)
    return normalized


def score_gift(gift: Gift, criteria: GiftCriteria) -> GiftScore:
    relationship = normalize_relationship(criteria.relationship)
    occasion = normalize_occasion(criteria.occasion)
    constraints = normalize_constraints(criteria.constraints)
    constraints.extend(_context_constraints(relationship, occasion, criteria.budget_krw))
    preference_terms = _terms(criteria.preferences)
    reasons: list[str] = []
    risks: list[str] = []
    score = 0.0

    if gift.price_krw <= criteria.budget_krw:
        budget_ratio = gift.price_krw / max(criteria.budget_krw, 1)
        if budget_ratio >= 0.55:
            score += 20
            reasons.append("예산을 충분히 활용하면서 과하지 않습니다.")
        else:
            score += 14
            reasons.append("예산 안에서 부담이 낮습니다.")
    else:
        over = gift.price_krw - criteria.budget_krw
        score -= 30
        risks.append(f"예산을 {over:,}원 초과합니다.")

    if occasion in gift.occasions:
        score += 28
        reasons.append(f"{criteria.occasion} 상황과 잘 맞습니다.")
    elif any(tag in gift.tags for tag in {"safe", "polite", "quick_pickup"}):
        score += 10
        reasons.append("상황이 애매해도 무난한 선택입니다.")

    if relationship in gift.relationships:
        score += 24
        reasons.append(f"{criteria.relationship}에게 주기 자연스럽습니다.")
    elif "friend" in gift.relationships or "coworker" in gift.relationships:
        score += 8
        reasons.append("관계가 달라도 부담이 적은 편입니다.")

    matched_preferences = sorted(set(preference_terms).intersection(gift.tags))
    if matched_preferences:
        score += min(12, 4 * len(matched_preferences))
        reasons.append("선호 조건과 맞습니다: " + ", ".join(matched_preferences))

    avoid_tokens = set(gift.avoid_for).intersection(constraints)
    if avoid_tokens:
        score -= 18
        risks.append("제약 조건과 충돌합니다: " + ", ".join(sorted(avoid_tokens)))

    risk_bonus = {"low": 10, "medium": 3, "high": -8}[gift.risk_level]
    score += risk_bonus
    if gift.risk_level == "low":
        reasons.append("실패 리스크가 낮습니다.")
    else:
        risks.append("취향에 따라 호불호가 있을 수 있습니다.")

    if "quick_pickup" in gift.tags:
        score += 8
        reasons.append("급한 픽업 상황에 적합합니다.")

    return GiftScore(
        gift_id=gift.id,
        score=score,
        reasons=reasons[:5],
        risk_notes=risks,
    )


def score_pickup_option(option: PickupOption) -> float:
    score = option.store.reliability_score * 20
    if option.route.feasible:
        score += 30
        score += min(15, max(0, option.route.arrival_margin_minutes))
    else:
        score -= 35

    score -= max(0, option.route.detour_minutes) * 1.2
    score -= option.route.pickup_wait_minutes * 0.8
    return score


def _normalize(value: str, aliases: dict[str, str]) -> str:
    folded = value.strip().casefold()
    if folded in aliases.values():
        return folded
    for needle, replacement in aliases.items():
        if needle.casefold() in folded:
            return replacement
    return folded.replace(" ", "_")


def _context_constraints(relationship: str, occasion: str, budget_krw: int) -> list[str]:
    constraints = [relationship, occasion, f"{relationship}_{occasion}"]
    if relationship in {"girlfriend", "boyfriend", "partner"} and occasion == "birthday":
        constraints.append("romantic_birthday")
    if budget_krw <= 20_000:
        constraints.append("low_budget")
    return constraints


def _terms(value: str) -> list[str]:
    return [
        term.strip().casefold()
        for term in re.split(r"[\s,;/]+", value)
        if term.strip()
    ]
