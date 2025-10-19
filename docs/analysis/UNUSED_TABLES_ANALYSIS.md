# 미사용 테이블 분석 및 삭제 제안

## 현재 데이터베이스 테이블 목록

### ✅ 사용 중인 테이블 (유지)

1. **stock_price** - 주식 가격 데이터
2. **stock_info** - 주식 정보
3. **investor_trading** - 투자자 거래 데이터
4. **market_data** - 시장 데이터
5. **data_collection_log** - 데이터 수집 로그
6. **collection_progress** - 수집 진행 상황
7. **data_quality_check** - 데이터 품질 체크

8. **block1_detection** - Block1 탐지 결과
9. **block2_detection** - Block2 탐지 결과
10. **block3_detection** - Block3 탐지 결과
11. **block4_detection** - Block4 탐지 결과
12. **block_pattern** - 블록 패턴 (Block1~4 연결)

13. **seed_condition_preset** - Seed 조건 프리셋 (통합)
14. **redetection_condition_preset** - Redetection 조건 프리셋 (통합)

### ❌ 미사용 테이블 (삭제 제안)

#### 1. block1_condition_preset
- **이유**: `seed_condition_preset`과 `redetection_condition_preset`에 통합됨
- **사용처**: 없음 (레거시)
- **데이터**: Block1 조건만 저장 (현재는 통합 조건 사용)

#### 2. block2_condition_preset
- **이유**: `seed_condition_preset`과 `redetection_condition_preset`에 통합됨
- **사용처**: 없음 (레거시)
- **데이터**: Block1+2 조건 저장 (현재는 통합 조건 사용)
- **스키마 문제**:
  - `block_volume_ratio`, `low_price_margin`, `min_candles_after_block1` (구 컬럼명)
  - 리팩토링 후 사용하지 않음

#### 3. block3_condition_preset
- **이유**: `seed_condition_preset`과 `redetection_condition_preset`에 통합됨
- **사용처**: 없음 (레거시)
- **데이터**: Block1+2+3 조건 저장 (현재는 통합 조건 사용)
- **스키마 문제**:
  - 중복 컬럼 존재 (`block2_*`와 구 컬럼명 `block_volume_ratio` 등)
  - 리팩토링 후 사용하지 않음

#### 4. block4_condition_preset
- **이유**: `seed_condition_preset`과 `redetection_condition_preset`에 통합됨
- **사용처**: 없음 (레거시)
- **데이터**: Block1+2+3+4 조건 저장 (현재는 통합 조건 사용)
- **생성 시점**: 최근 (Block4 기능 추가 시)
- **상태**: 사용된 적 없음

## 테이블 통합 현황

### Before (리팩토링 전)
```
block1_condition_preset  →  Block1만 저장
block2_condition_preset  →  Block1 참조 + Block2 추가
block3_condition_preset  →  Block2 참조 + Block3 추가
block4_condition_preset  →  Block3 참조 + Block4 추가
```

### After (리팩토링 후)
```
seed_condition_preset         →  Block1~4 모든 조건을 독립 필드로 저장
redetection_condition_preset  →  Block1~4 모든 조건을 독립 필드로 저장
```

## 삭제 계획

### Phase 1: 데이터 백업 (선택)
```sql
-- 혹시 모를 데이터가 있다면 백업
.output backup_block_conditions.sql
.dump block1_condition_preset
.dump block2_condition_preset
.dump block3_condition_preset
.dump block4_condition_preset
.output stdout
```

### Phase 2: 테이블 삭제
```sql
DROP TABLE IF EXISTS block1_condition_preset;
DROP TABLE IF EXISTS block2_condition_preset;
DROP TABLE IF EXISTS block3_condition_preset;
DROP TABLE IF EXISTS block4_condition_preset;
```

### Phase 3: Repository 파일 삭제
```bash
# Repository 파일들
rm src/infrastructure/repositories/block1_condition_preset_repository.py
rm src/infrastructure/repositories/block2_condition_preset_repository.py
rm src/infrastructure/repositories/block3_condition_preset_repository.py
rm src/infrastructure/repositories/block4_condition_preset_repository.py
```

### Phase 4: Import 정리
```python
# src/infrastructure/repositories/__init__.py 에서 제거
- from .block1_condition_preset_repository import Block1ConditionPresetRepository
- from .block2_condition_preset_repository import Block2ConditionPresetRepository
- from .block3_condition_preset_repository import Block3ConditionPresetRepository
- from .block4_condition_preset_repository import Block4ConditionPresetRepository

# __all__ 에서 제거
- 'Block1ConditionPresetRepository',
- 'Block2ConditionPresetRepository',
- 'Block3ConditionPresetRepository',
- 'Block4ConditionPresetRepository',
```

## 영향도 분석

### 코드 사용처 검색 결과
```bash
# Repository 클래스 사용처 검색
grep -r "Block[1-4]ConditionPresetRepository" --include="*.py"
```

**결과**: 정의 파일과 `__init__.py` 외에 사용처 없음 ✅

### 테이블 데이터 확인
```sql
-- 각 테이블에 데이터가 있는지 확인
SELECT COUNT(*) FROM block1_condition_preset;
SELECT COUNT(*) FROM block2_condition_preset;
SELECT COUNT(*) FROM block3_condition_preset;
SELECT COUNT(*) FROM block4_condition_preset;
```

## 삭제 권장 사항

### ✅ 안전하게 삭제 가능
- 모든 기능이 `seed_condition_preset`과 `redetection_condition_preset`으로 이관됨
- 코드에서 참조하는 곳 없음
- 리팩토링 완료로 더 이상 필요 없음

### ⚠️ 주의 사항
- 삭제 전 각 테이블의 데이터 확인 권장
- 만약 커스텀 프리셋이 있다면 수동으로 통합 테이블로 이전 필요

## 실행 방법

```bash
# 마이그레이션 스크립트 실행
python migrate_drop_legacy_condition_tables.py

# 또는 수동 실행
sqlite3 data/database/stock_data.db < drop_legacy_tables.sql
```
