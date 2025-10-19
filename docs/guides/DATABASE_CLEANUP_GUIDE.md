# 데이터베이스 정리 가이드

## 완료된 작업 ✅

### 1. Block4 컬럼 추가
```bash
python migrate_add_block4_columns.py
```

**추가된 컬럼:**
- `seed_condition_preset`: block4_volume_ratio, block4_low_price_margin, block4_min_candles_after_block3
- `redetection_condition_preset`: 위 3개 + block4_tolerance_pct

### 2. 프리셋 데이터 업데이트
```bash
python update_presets_from_json.py
```

**업데이트된 프리셋:**
- Seed: aggressive_seed, standard_seed, conservative_seed
- Redetection: aggressive_redetect, standard_redetect, conservative_redetect

**업데이트 내용:**
- Block4 관련 값 반영 (volume_ratio=20.0%, low_price_margin=10.0%, min_candles=4)
- JSON 파일의 모든 조건값 DB에 동기화

### 3. 테스트 완료
```bash
python test_ananti_full_detection.py
```

**결과:** ✅ 정상 동작 확인 (5개 Block1 Seed 탐지)

---

## 미사용 테이블 분석

### 삭제 대상 테이블 (4개)

| 테이블 | 데이터 | 상태 | 삭제 이유 |
|--------|--------|------|-----------|
| `block1_condition_preset` | 1건 | 🗑️ 삭제 권장 | seed/redetection 테이블로 통합됨 |
| `block2_condition_preset` | 1건 | 🗑️ 삭제 권장 | seed/redetection 테이블로 통합됨 |
| `block3_condition_preset` | 1건 | 🗑️ 삭제 권장 | seed/redetection 테이블로 통합됨 |
| `block4_condition_preset` | 0건 | 🗑️ 삭제 권장 | 생성 후 한 번도 사용 안 함 |

### 코드 사용처 분석 결과

```bash
# Repository 파일 존재
✅ src/infrastructure/repositories/block1_condition_preset_repository.py
✅ src/infrastructure/repositories/block2_condition_preset_repository.py
✅ src/infrastructure/repositories/block3_condition_preset_repository.py
✅ src/infrastructure/repositories/block4_condition_preset_repository.py

# 실제 사용처
❌ 없음 (레거시 코드)
```

**결론:** 안전하게 삭제 가능

---

## 테이블 삭제 절차

### Step 1: 백업 및 테이블 삭제 (자동)

```bash
python migrate_drop_legacy_condition_tables.py
```

**실행 내용:**
1. 백업 파일 생성: `data/database/backup_legacy_condition_tables.sql`
2. 4개 테이블 삭제
3. 삭제 전 확인 메시지 표시

**확인 메시지 예시:**
```
⚠️  WARNING: This will permanently delete the following tables:
  - block1_condition_preset
  - block2_condition_preset
  - block3_condition_preset
  - block4_condition_preset

Do you want to continue? (yes/no):
```

### Step 2: Repository 파일 삭제 (수동)

```bash
# 4개 파일 삭제
rm src/infrastructure/repositories/block1_condition_preset_repository.py
rm src/infrastructure/repositories/block2_condition_preset_repository.py
rm src/infrastructure/repositories/block3_condition_preset_repository.py
rm src/infrastructure/repositories/block4_condition_preset_repository.py
```

### Step 3: Import 정리 (수동)

[src/infrastructure/repositories/__init__.py](../src/infrastructure/repositories/__init__.py) 파일에서 제거:

```python
# 삭제할 import
from .block1_condition_preset_repository import Block1ConditionPresetRepository
from .block2_condition_preset_repository import Block2ConditionPresetRepository
from .block3_condition_preset_repository import Block3ConditionPresetRepository
from .block4_condition_preset_repository import Block4ConditionPresetRepository

# __all__ 리스트에서 제거
__all__ = [
    # ...
    # 'Block1ConditionPresetRepository',  # 삭제
    # 'Block2ConditionPresetRepository',  # 삭제
    # 'Block3ConditionPresetRepository',  # 삭제
    # 'Block4ConditionPresetRepository',  # 삭제
    # ...
]
```

### Step 4: 최종 테스트

```bash
# 전체 패턴 탐지 테스트
python test_ananti_full_detection.py

# 프리셋 로드 테스트
python -c "
from src.infrastructure.repositories.seed_condition_preset_repository import SeedConditionPresetRepository
from src.infrastructure.database.connection import DatabaseConnection

db = DatabaseConnection('data/database/stock_data.db')
repo = SeedConditionPresetRepository(db)
preset = repo.load('aggressive_seed')
print(f'✅ Seed preset loaded: {preset}')
print(f'   Block4 volume ratio: {preset.block4_volume_ratio}%')
print(f'   Block4 low margin: {preset.block4_low_price_margin}%')
print(f'   Block4 min candles: {preset.block4_min_candles_after_block3}')
"
```

---

## 데이터베이스 최종 구조

### 현재 사용 중인 Preset 테이블

#### 1. seed_condition_preset
**용도:** Block1~4 Seed 탐지 조건

**주요 컬럼:**
```
- Block1 조건 (11개): entry_surge_rate, entry_ma_period, ... exit_ma_period, cooldown_days
- Block2 조건 (3개): block2_volume_ratio, block2_low_price_margin, block2_min_candles_after_block1
- Block3 조건 (3개): block3_volume_ratio, block3_low_price_margin, block3_min_candles_after_block2
- Block4 조건 (3개): block4_volume_ratio, block4_low_price_margin, block4_min_candles_after_block3
```

**현재 프리셋:** aggressive_seed, standard_seed, conservative_seed

#### 2. redetection_condition_preset
**용도:** Block1~4 재탐지 조건

**주요 컬럼:**
```
- Block1 조건 (11개): 위와 동일
- Block2 조건 (3개): 위와 동일
- Block3 조건 (3개): 위와 동일
- Block4 조건 (3개): 위와 동일
- Tolerance (4개): block1_tolerance_pct, block2_tolerance_pct, block3_tolerance_pct, block4_tolerance_pct
```

**현재 프리셋:** aggressive_redetect, standard_redetect, conservative_redetect

---

## 참고 문서

- [UNUSED_TABLES_ANALYSIS.md](UNUSED_TABLES_ANALYSIS.md) - 미사용 테이블 상세 분석
- [REFACTORING_TODO.md](REFACTORING_TODO.md) - 리팩토링 히스토리

---

## 요약

1. ✅ Block4 컬럼 추가 완료
2. ✅ JSON → DB 프리셋 업데이트 완료
3. ✅ 테스트 통과
4. ⏳ 레거시 테이블 삭제 준비 완료 (실행 대기)

**다음 단계:** `python migrate_drop_legacy_condition_tables.py` 실행
