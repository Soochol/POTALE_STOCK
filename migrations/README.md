# 마이그레이션 스크립트

데이터베이스 스키마 및 데이터 마이그레이션 스크립트 모음

---

## 🎯 최신 마이그레이션 (2025-10-22)

### ✅ migrate_unified_schema_update.py
**통합 스키마 업데이트** - 모든 preset 테이블을 최신 상태로 마이그레이션

**변경 내용:**
- `*_volume_high_months` → `*_volume_high_days` (개월 → 일 단위)
- `*_price_high_months` → `*_price_high_days` (개월 → 일 단위)

**실행:**
```bash
python migrations/migrate_unified_schema_update.py
```

**상태:** ✅ 적용 완료

---

## 📋 스크립트 목록

### Preset 관련
- `check_preset_names.py` - 프리셋 이름 확인
- `check_preset_sync.py` - 프리셋 동기화 확인
- `recreate_preset_tables.py` - 프리셋 테이블 재생성

### 최근 스키마 변경 (2024-2025)
- ✅ `migrate_unified_schema_update.py` - **최신** months→days 통합 마이그레이션
- ⚠️  `migrate_rename_months_to_days.py` - (통합 마이그레이션으로 대체됨)
- ✅ `migrate_rename_cooldown_to_min_start_interval.py` - cooldown→min_start_interval 이름 변경
- ✅ `migrate_remove_high_above_ma.py` - high_above_ma 컬럼 제거
- ✅ `migrate_nullable_entry_conditions.py` - 진입 조건 필드 nullable 변경
- ✅ `migrate_add_redetection_period_columns.py` - 재탐지 기간 컬럼 추가

### 파라미터 수정 (히스토리)
- `fix_blockN_specific_params.py` - BlockN 특정 파라미터 수정
- `fix_double_block1_prefix.py` - 중복 block1 prefix 수정
- `migrate_add_block1_prefix.py` - block1 prefix 추가
- `migrate_add_blockN_all_params.py` - BlockN 전체 파라미터 추가
- `migrate_rename_block23_params.py` - Block2/3 파라미터 이름 변경
- `migrate_rename_entry_params.py` - Entry 파라미터 이름 변경
- `migrate_reorder_preset_columns.py` - 프리셋 컬럼 순서 재정렬
- `migrate_drop_unused_candle_columns.py` - 미사용 캔들 컬럼 삭제
- `migrate_add_peak_volume_to_block1.py` - Block1 peak_volume 추가

### 테이블 변경 (히스토리)
- `migrate_add_block4_columns.py` - Block4 컬럼 추가
- `migrate_drop_legacy_condition_tables.py` - 레거시 조건 테이블 삭제

---

## 📊 현재 스키마 상태 (2025-10-22)

### seed_condition_preset
- ✅ `block1/2/3/4_entry_volume_high_days` (일 단위)
- ✅ `block1/2/3/4_entry_price_high_days` (일 단위)
- ✅ `block1/2/3/4_min_start_interval_days`
- ✅ `high_above_ma` 제거됨
- ✅ Block2/3/4 min/max_candles_after 포함

### redetection_condition_preset
- ✅ `block1/2/3/4_entry_volume_high_days` (일 단위)
- ✅ `block1/2/3/4_entry_price_high_days` (일 단위)
- ✅ `block1/2/3/4_min_start_interval_days`
- ✅ `block2/3/4_min_candles_after_block1/2/3`
- ✅ `block2/3/4_max_candles_after_block1/2/3`
- ✅ Tolerance와 redetection 기간 필드 포함

### 모델/엔티티 일치성
- ✅ `SeedConditionPreset` 모델 ↔ DB
- ✅ `RedetectionConditionPreset` 모델 ↔ DB
- ✅ `SeedCondition` 엔티티 ↔ 모델
- ✅ `RedetectionCondition` 엔티티 ↔ 모델

---

## 🔧 사용 방법

```bash
# 데이터베이스 백업 (필수!)
cp data/database/stock_data.db data/database/stock_data_backup_$(date +%Y%m%d).db

# 마이그레이션 실행
python migrations/migrate_unified_schema_update.py

# 검증
python scripts/update_presets_from_yaml.py
```

## ⚠️  주의사항

- **백업 필수**: 마이그레이션 실행 전 반드시 데이터베이스 백업
- **한 번만 실행**: 동일한 마이그레이션 재실행 시 오류 발생 가능
- **순서 중요**: 일부 마이그레이션은 실행 순서가 중요함
- **검증**: 마이그레이션 후 `update_presets_from_yaml.py` 실행으로 검증
