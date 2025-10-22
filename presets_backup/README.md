# Preset 설정 파일 (JSON)

패턴 재탐지 시스템의 Seed 조건과 Redetection 조건을 JSON 파일로 관리합니다.

## 📁 파일 구조

```
presets/
├── seed_conditions.json          # Seed 조건 (엄격한 초기 탐지)
├── redetection_conditions.json   # Redetection 조건 (완화된 재탐지)
└── README.md                      # 이 파일
```

## 🔧 사용법

### 1. JSON 파일 수정

JSON 파일을 직접 수정하여 조건 값을 변경합니다.

**seed_conditions.json 예시:**
```json
{
  "aggressive_seed": {
    "description": "공격적 Seed 조건 (엄격한 기준)",
    "entry_surge_rate": 8.0,
    "entry_ma_period": 120,
    "exit_ma_period": 120,
    "volume_high_months": 12,
    "price_high_months": 2,
    "cooldown_days": 20,
    "block2_volume_ratio": 15.0,
    "block2_low_price_margin": 10.0,
    "block3_volume_ratio": 15.0,
    "block3_low_price_margin": 10.0
  }
}
```

### 2. DB에 업데이트

수정한 JSON 파일을 DB에 반영합니다.

```bash
# 모든 preset 업데이트
python update_presets_from_json.py

# Seed 조건만 업데이트
python update_presets_from_json.py --seed-only

# Redetection 조건만 업데이트
python update_presets_from_json.py --redetect-only

# 미리보기 (실제 저장 안 함)
python update_presets_from_json.py --dry-run
```

### 3. 커스텀 파일 경로 사용

```bash
python update_presets_from_json.py --seed-file my_seeds.json --redetect-file my_redetects.json
```

## 📋 파라미터 설명

### Seed Condition 파라미터

| 파라미터 | 타입 | 설명 | 예시 |
|---------|------|------|------|
| `entry_surge_rate` | float | 진입 등락률 (%) | `8.0` = 8% 이상 |
| `entry_ma_period` | int | 진입 이동평균선 기간 (일) | `120` = 120일선 |
| `exit_ma_period` | int | 종료 이동평균선 기간 (일) | `120` = 120일선 |
| `volume_high_months` | int | 신고거래량 기간 (개월) | `12` = 12개월 |
| `price_high_months` | int | 신고가 기간 (개월) | `2` = 2개월 |
| `cooldown_days` | int | Cooldown 기간 (일) | `20` = 20일 |
| `block2_volume_ratio` | float | Block2 거래량 비율 (%) | `15.0` = 15% |
| `block2_low_price_margin` | float | Block2 저가 마진 (%) | `10.0` = 10% |
| `block3_volume_ratio` | float | Block3 거래량 비율 (%) | `15.0` = 15% |
| `block3_low_price_margin` | float | Block3 저가 마진 (%) | `10.0` = 10% |

### Redetection Condition 파라미터

Seed Condition의 모든 파라미터 + 아래 추가 파라미터:

| 파라미터 | 타입 | 설명 | 예시 |
|---------|------|------|------|
| `block1_tolerance_pct` | float | Block1 가격 범위 (%) | `10.0` = ±10% |
| `block2_tolerance_pct` | float | Block2 가격 범위 (%) | `15.0` = ±15% |
| `block3_tolerance_pct` | float | Block3 가격 범위 (%) | `20.0` = ±20% |

## 🎯 Preset 종류

### Seed Conditions (초기 탐지)

1. **aggressive_seed**: 엄격한 기준 (진입 등락률 8%)
2. **standard_seed**: 표준 기준 (진입 등락률 6%)
3. **conservative_seed**: 완화된 기준 (진입 등락률 5%, 신고거래량 6개월)

### Redetection Conditions (재탐지)

1. **aggressive_redetect**: 상대적으로 엄격 (진입 등락률 5%, Tolerance 10/15/20%)
2. **standard_redetect**: 표준 (진입 등락률 4%, Tolerance 12/17/22%)
3. **conservative_redetect**: 가장 완화 (진입 등락률 3%, Tolerance 15/20/25%)

## ⚙️ 조건 조합 예시

### 공격적 패턴 탐지
```bash
# conservative_seed (5% 등락률) + conservative_redetect (3% 등락률, 15/20/25% tolerance)
# → 더 많은 패턴 탐지, 정확도는 낮음
```

### 보수적 패턴 탐지
```bash
# aggressive_seed (8% 등락률) + aggressive_redetect (5% 등락률, 10/15/20% tolerance)
# → 적은 패턴 탐지, 정확도는 높음
```

### 균형잡힌 탐지
```bash
# standard_seed (6% 등락률) + standard_redetect (4% 등락률, 12/17/22% tolerance)
# → 중간 수준의 패턴 탐지
```

## 📌 참고사항

1. **JSON 형식 준수**: 쉼표, 중괄호 등 JSON 문법을 정확히 지켜야 합니다.
2. **float vs int**: 소수점이 있으면 float (예: `8.0`), 없으면 int (예: `120`)
3. **dry-run 먼저**: 변경 전 `--dry-run`으로 미리보기 권장
4. **백업**: 중요한 변경 전 JSON 파일 백업 권장

## 🔍 디버깅

업데이트가 제대로 되었는지 확인:

```python
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.repositories.seed_condition_preset_repository import SeedConditionPresetRepository

db = DatabaseConnection("data/database/stock_data.db")
repo = SeedConditionPresetRepository(db)

# 조건 로드
condition = repo.load("standard_seed")
print(condition)
```
