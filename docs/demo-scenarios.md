# Demo Scenarios

## Scenario 1: Romantic Birthday

Prompt:

```text
지금 강남역에서 판교역으로 여자친구 생일 약속 가는 중이야.
35분 안에 도착해야 하고 예산은 3만원이야.
가는 길에 픽업 가능한 선물 추천해줘.
```

Expected direction:

- mini flower bouquet + dessert
- high relationship fit
- low risk
- clear pickup route
- warm short message

30분으로 줄이면 픽업이 어렵다는 fallback을 보여주는 실패 처리 데모로 사용한다.

## Scenario 2: Manager Housewarming

Prompt:

```text
상사 집들이에 가는 길이야. 부담스럽지 않게 2만원 이하로 살 수 있는 선물 추천해줘.
```

Expected direction:

- practical home item
- avoid overly personal gifts
- polite message
- explain risk reduction

## Scenario 3: Apology Visit

Prompt:

```text
친구한테 사과하러 가는 중이야. 15분 정도 여유 있고 너무 장난스럽지 않은 선물이 필요해.
```

Expected direction:

- dessert, tea, or small flower
- sincere tone
- avoid flashy romantic gifts

## Scenario 4: Parent Visit

Prompt:

```text
부모님 집에 들르는데 빈손으로 가긴 그래. 4만원 안에서 지금 픽업 가능한 걸로 추천해줘.
```

Expected direction:

- fruit, dessert, tea, health-friendly gift
- avoid trendy novelty items

## Scenario 5: Impossible Timing

Prompt:

```text
5분 뒤 도착해야 하는데 중간에 선물 살 수 있어?
```

Expected direction:

- say pickup is not feasible
- recommend mobile gift/message fallback
- avoid pretending a store stop is possible
