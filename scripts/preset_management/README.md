# Preset Management Scripts

규칙 기반 탐지 조건 프리셋 관리 스크립트

## 스크립트 목록

### update_presets_from_yaml.py
**목적**: YAML 파일의 프리셋을 데이터베이스에 업데이트

**특징**:
- Seed 조건 및 Redetection 조건 업데이트
- Dry-run 모드 지원 (미리보기)
- 변경사항 상세 출력

**사용법**:
```bash
# 모든 프리셋 업데이트
python scripts/preset_management/update_presets_from_yaml.py

# Seed 조건만 업데이트
python scripts/preset_management/update_presets_from_yaml.py --seed-only

# Redetection 조건만 업데이트
python scripts/preset_management/update_presets_from_yaml.py --redetect-only

# 미리보기 (실제 저장 안 함)
python scripts/preset_management/update_presets_from_yaml.py --dry-run
```

**워크플로우**:
1. YAML 파일 수정 (`presets/seed_conditions.yaml`, `presets/redetection_conditions.yaml`)
2. 스크립트 실행 (dry-run으로 먼저 확인)
3. DB에 반영됨
4. 탐지 스크립트가 새 프리셋 사용

---

### load_presets.py
**목적**: 데이터베이스의 프리셋 확인 및 검증

**특징**:
- 현재 DB에 저장된 프리셋 출력
- 프리셋 값 검증
- YAML과 DB 동기화 상태 확인

**사용법**:
```bash
# 모든 프리셋 출력
python scripts/preset_management/load_presets.py

# 특정 프리셋만 출력
python scripts/preset_management/load_presets.py --name default_seed
```

---

## 프리셋 시스템

### Preset 종류

**Seed Conditions (초기 탐지)**:
- `aggressive_seed`: 엄격한 기준 (진입 등락률 8%)
- `standard_seed`: 표준 기준 (진입 등락률 6%)
- `conservative_seed`: 완화된 기준 (진입 등락률 5%)

**Redetection Conditions (재탐지)**:
- `aggressive_redetect`: 상대적으로 엄격 (진입 등락률 5%)
- `standard_redetect`: 표준 (진입 등락률 4%)
- `conservative_redetect`: 가장 완화 (진입 등락률 3%)

### 주요 파라미터

**진입 조건**:
- `entry_surge_rate`: 진입 등락률 (%)
- `entry_ma_period`: 진입 이동평균선 기간 (일)
- `entry_min_trading_value`: 최소 거래대금 (억)
- `entry_volume_high_months`: 신고거래량 기간 (개월)

**종료 조건**:
- `exit_ma_period`: 종료 이동평균선 기간 (일)

**블록 간격**:
- `min_start_interval_days`: 블록 시작 최소 간격 (일)

## 참고

- [프리셋 설정 가이드](../../presets/README.md)
- [블록 탐지 시스템](../../docs/specification/BLOCK_DETECTION.md)
