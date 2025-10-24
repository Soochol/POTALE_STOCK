# Legacy Scripts (Archived)

이 폴더에는 기존 block1~4_detection 테이블 시스템을 사용하던 스크립트들이 보관되어 있습니다.

## ⚠️ 더 이상 작동하지 않습니다

2025년 10월 24일, 프로젝트가 **Dynamic Block Detection 시스템**으로 전환되면서 다음 변경사항이 발생했습니다:

### 삭제된 테이블
- `block1_detection`, `block2_detection`, `block3_detection`, `block4_detection`
- `block5_detection`, `block6_detection`
- `block_pattern`
- `block_label`
- `seed_condition_preset`, `redetection_condition_preset`

### 삭제된 Repository
- `Block1Repository`, `Block2Repository`, `Block3Repository`, `Block4Repository`
- `SeedConditionPresetRepository`, `RedetectionConditionPresetRepository`

### 새 시스템으로 대체됨
이 스크립트들은 **YAML 기반 Dynamic Block Detection 시스템**으로 대체되었습니다:
- **새 테이블**: `dynamic_block_detection` (단일 테이블, JSON 기반)
- **새 Repository**: `DynamicBlockRepositoryImpl`
- **새 스크립트**: `scripts/rule_based_detection/detect_patterns.py`

## 📁 보관된 파일들

### 1. debug_block1_detection.py
Block1 탐지 디버깅용 스크립트. Block1Repository를 사용합니다.

**기존 사용법**:
```bash
python scripts/rule_based_detection/debug_block1_detection.py --ticker 025980
```

**대체 방법**:
```bash
python scripts/rule_based_detection/detect_patterns.py \
    --ticker 025980 \
    --config presets/examples/simple_pattern_example.yaml \
    --verbose
```

---

### 2. test_seed_detector_2020.py
2020년 데이터로 Seed 탐지를 테스트하는 스크립트.

**기존 사용법**:
```bash
python scripts/rule_based_detection/test_seed_detector_2020.py
```

**대체 방법**:
```bash
python scripts/rule_based_detection/detect_patterns.py \
    --ticker 025980 \
    --config presets/examples/extended_pattern_example.yaml \
    --from-date 2020-01-01 \
    --to-date 2020-12-31
```

---

## 🔧 새 시스템 사용 가이드

새 시스템으로 마이그레이션하려면 [USER_GUIDE.md](../../../USER_GUIDE.md)를 참고하세요.

### Quick Start
```bash
# 1. YAML 설정 파일 작성
cp presets/examples/extended_pattern_example.yaml presets/my_pattern.yaml

# 2. 블록 탐지 실행
python scripts/rule_based_detection/detect_patterns.py \
    --ticker 025980 \
    --config presets/my_pattern.yaml

# 3. 결과 확인
sqlite3 data/database/stock_data.db "SELECT * FROM dynamic_block_detection WHERE ticker='025980';"
```

---

## 📚 참고 문서
- [USER_GUIDE.md](../../../USER_GUIDE.md) - 새 시스템 사용 가이드
- [BLOCK_DETECTION.md](../../specification/BLOCK_DETECTION.md) - 블록 탐지 시스템 사양
- [extended_pattern_example.yaml](../../../presets/examples/extended_pattern_example.yaml) - YAML 설정 예제

---

**보관 날짜**: 2025-10-24
**이유**: Dynamic Block Detection 시스템 전환
