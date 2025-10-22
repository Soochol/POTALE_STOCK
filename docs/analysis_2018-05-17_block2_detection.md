# 2018-05-17 Block2 탐지 실패 원인 분석 및 해결

## 요약 (Executive Summary)

**문제**: 2018-05-17이 Block2 Seed로 탐지되지 않고, 대신 2018-05-21이 탐지됨
**원인**: 거래정지 기간(2018-04-30 ~ 2018-05-16) 이후 `get_previous_trading_day_stock()` 함수가 거래량 0인 날짜를 반환하여 조건 실패
**해결**: 함수 수정하여 거래량 0인 날짜를 자동으로 스킵하도록 개선
**결과**: 2018-05-17이 정상적으로 Block2 Seed로 탐지됨

---

## 1. 문제 상황

### Pattern #1 탐지 결과 (수정 전)
```
Pattern #1
├── Block1 Seed: 2018-03-07 ~ 2018-06-27
│   ├── 진입가: 6,230원
│   ├── 최고가: 7,460원
├── Block2 Seed: 2018-05-21 ~ 2018-06-27  ← 왜 2018-05-17이 아닌가?
│   ├── 진입가: 10,500원
│   ├── 최고가: 11,450원
```

### 주가 데이터
| 날짜 | 종가 | 거래량 | 비고 |
|------|------|--------|------|
| 2018-04-27 | 7,540 | 2,056,565 | 정상 거래 마지막 날 |
| 2018-04-30 ~ 05-16 | 7,540 | **0** | **거래정지 기간** |
| **2018-05-17** | 9,400 | 16,164,141 | **거래 재개** |
| 2018-05-18 | 8,980 | 4,934,905 | |
| 2018-05-21 | 10,500 | 18,257,495 | Block2 Seed로 탐지됨 |

---

## 2. 원인 분석

### 2.1 디버그 스크립트 실행 결과

**2018-05-17 (수정 전):**
```
Stock Data:
  High: 9,800, Low: 8,930, Close: 9,400
  Volume: 16,164,141
  Rate: 29.97%
  MA_60: 6,889
  Trading Value: 1,519억

Previous Trading Day: 2018-05-16  ← 문제!
Prev Volume: 0                     ← volume = 0
Volume Spike Ratio: 0.0% (required: 120.0%)

❌ FAILED - 2018-05-17 NOT DETECTED
```

**2018-05-21 (수정 전):**
```
Stock Data:
  High: 11,450, Low: 9,150, Close: 10,500
  Volume: 18,257,495
  Rate: 27.51%
  MA_60: 7,031
  Trading Value: 1,917억

Previous Trading Day: 2018-05-18   ← 정상 거래일
Prev Volume: 4,934,905
Volume Spike Ratio: 370.0% (required: 120.0%)

✓ OK - 2018-05-21 WOULD BE DETECTED
```

### 2.2 실패 조건 식별

Block2Checker의 조건 6 실패:
```python
# 조건 6: 전날 거래량 대비 N% 수준
if condition.base.block1_entry_volume_spike_ratio is not None:
    prev_stock = get_previous_trading_day_stock(stock.date, all_stocks)
    if prev_stock is None or prev_stock.volume <= 0:
        return False  ← 여기서 실패!
```

### 2.3 근본 원인

`get_previous_trading_day_stock()` 함수 (수정 전):
```python
def get_previous_trading_day_stock(current_date: date, all_stocks: List[Stock]) -> Optional[Stock]:
    # 현재 날짜 이전의 모든 Stock 필터링
    prev_stocks = [s for s in all_stocks if s.date < current_date]

    if not prev_stocks:
        return None

    # 가장 최근 거래일 반환
    return max(prev_stocks, key=lambda s: s.date)  ← volume 체크 없음!
```

**문제점:**
- 함수 주석에는 "거래정지를 자동으로 건너뛴다"고 명시되어 있음
- 그러나 실제로는 volume=0인 날짜를 필터링하지 않음
- 결과적으로 2018-05-16 (volume=0)을 반환
- Block2 조건 검사에서 즉시 실패

---

## 3. 해결 방법

### 3.1 함수 수정

[src/application/services/common/utils.py:40-41](../src/application/services/common/utils.py#L40-L41)

```python
def get_previous_trading_day_stock(current_date: date, all_stocks: List[Stock]) -> Optional[Stock]:
    """
    현재 날짜 이전의 가장 최근 거래일 Stock 반환

    거래일 Gap(공휴일, 거래정지)을 자동으로 건너뛰고
    실제 마지막 거래일의 데이터를 반환합니다.
    """
    # 현재 날짜 이전의 모든 Stock 필터링 (거래량 > 0인 것만)
    prev_stocks = [s for s in all_stocks if s.date < current_date and s.volume > 0]

    if not prev_stocks:
        return None

    # 가장 최근 거래일 반환 (날짜 기준 max)
    return max(prev_stocks, key=lambda s: s.date)
```

**변경 사항:**
- `s.volume > 0` 조건 추가
- 거래량이 0인 날짜는 자동으로 필터링됨
- 함수 docstring의 의도대로 거래정지일을 건너뜀

### 3.2 검증 결과

**2018-05-17 (수정 후):**
```
Previous Trading Day: 2018-04-27  ← 거래정지 기간 스킵!
Prev Volume: 2,056,565
Volume Spike Ratio: 786.0% (required: 120.0%)

✓ OK - 2018-05-17 WOULD BE DETECTED
```

---

## 4. 수정 후 패턴 탐지 결과

### Pattern #1 (수정 후)
```
Pattern #1
├── Block1 Seed: 2018-03-07 ~ 2018-06-27
│   ├── 진입가: 6,230원
│   ├── 최고가: 7,460원
├── Block2 Seed: 2018-05-17 ~ 2018-06-27  ← ✓ 수정됨!
│   ├── 진입가: 9,400원
│   ├── 최고가: 9,800원 (+4.3%)
│   └── Block2 재탐지: 1개
├── Block3 Seed: 2018-06-01 ~ 2018-06-27
│   ├── 진입가: 10,700원
│   ├── 최고가: 12,450원
```

### 비교표

| 항목 | 수정 전 | 수정 후 |
|------|---------|---------|
| Block2 Seed 시작일 | 2018-05-21 | **2018-05-17** |
| Block2 Seed 진입가 | 10,500원 | **9,400원** |
| Block2 Seed 최고가 | 11,450원 | **9,800원** |
| Previous Trading Day | 2018-05-18 | **2018-04-27** |
| Volume Spike Ratio | 370% | **786%** |

**개선 효과:**
- ✅ 더 빠른 진입 (2018-05-17이 2018-05-21보다 4일 빠름)
- ✅ 더 낮은 진입가 (9,400원 vs 10,500원)
- ✅ 더 강한 거래량 신호 (786% vs 370%)

---

## 5. 영향 범위

### 5.1 수정된 파일
- [src/application/services/common/utils.py](../src/application/services/common/utils.py) - `get_previous_trading_day_stock()` 함수

### 5.2 영향받는 기능
이 함수를 사용하는 모든 Block 탐지 로직:
- Block2Checker.check_entry() - Block2 진입 조건 검사
- Block3Checker, Block4Checker 등 (동일한 volume_spike_ratio 체크 사용)

### 5.3 잠재적 부작용
**거래정지 이후 재개 시점:**
- 이전: 거래정지 직후 첫 날은 자동으로 탐지 제외됨
- 현재: 거래정지 이전 마지막 거래일과 비교하여 정상적으로 탐지 가능
- 영향: **긍정적** - 거래 재개 시점의 급등주를 놓치지 않음

**완전히 신규 상장된 종목:**
- 상장 첫날의 경우 이전 거래 데이터가 없음
- `prev_stocks`가 빈 리스트가 되어 None 반환
- Block2Checker에서 `prev_stock is None` 체크로 실패
- 영향: **중립** - 기존과 동일하게 처리됨

---

## 6. 권장 사항

### 6.1 즉시 적용
✅ 수정 사항을 바로 반영 (이미 완료)

### 6.2 추가 테스트
다음 케이스들도 검증 권장:
1. ✅ 거래정지 이후 재개 (2018-05-17) - 완료
2. ⬜ 장기 거래정지 후 재개 (1개월 이상)
3. ⬜ 여러 번 반복되는 거래정지
4. ⬜ 신규 상장 종목 첫 거래일

### 6.3 문서화
- ✅ 함수 docstring 업데이트 (완료)
- ✅ Example 추가하여 volume=0 스킵 동작 명시 (완료)

---

## 7. 결론

### 문제 해결 완료
2018-05-17이 Block2 Seed로 정상적으로 탐지되지 않던 문제를 완전히 해결했습니다.

### 핵심 개선사항
1. **정확성**: 거래정지 기간을 올바르게 처리
2. **신뢰성**: 함수 동작이 docstring과 일치
3. **성능**: 거래 재개 시점의 강력한 신호를 놓치지 않음

### 향후 모니터링
- 다른 종목의 거래정지 케이스 발생 시 정상 탐지되는지 확인
- Volume spike ratio 조건이 의도대로 작동하는지 지속 검증

---

**작성일**: 2025-10-22
**분석자**: Claude Code
**관련 이슈**: 2018-05-17 Block2 Seed 미탐지
**해결 PR**: (해당시 PR 번호 기록)
