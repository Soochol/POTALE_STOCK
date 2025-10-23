# Rule-based Detection Scripts

규칙 기반 블록 패턴 탐지 시스템

## 스크립트 목록

### detect_patterns.py
**목적**: 블록 패턴 탐지 메인 스크립트 (Seed + Redetection)

**특징**:
- Seed 탐지 + 5년 재탐지 통합 실행
- 단일/다중 종목 지원
- 프리셋 선택 가능
- Rich 라이브러리로 결과 시각화
- 데이터베이스에 자동 저장

**사용법**:
```bash
# 기본: 아난티(025980) 전체 기간 탐지
python scripts/rule_based_detection/detect_patterns.py --ticker 025980

# 다중 종목
python scripts/rule_based_detection/detect_patterns.py --ticker 025980,005930,035720

# 기간 지정
python scripts/rule_based_detection/detect_patterns.py --ticker 025980 --from-date 2020-01-01

# 다른 프리셋 사용
python scripts/rule_based_detection/detect_patterns.py --ticker 025980 --seed-preset strict_seed

# 상세 출력
python scripts/rule_based_detection/detect_patterns.py --ticker 025980 --verbose

# 미리보기만 (저장 안 함)
python scripts/rule_based_detection/detect_patterns.py --ticker 025980 --dry-run
```

---

### debug_block1_detection.py
**목적**: Block1 탐지 디버깅 도구

**특징**:
- 특정 날짜의 Block1 조건 확인
- 각 조건별 통과/실패 상세 출력
- 문제 진단 및 프리셋 튜닝에 유용

**사용법**:
```bash
# 특정 종목 Block1 디버깅
python scripts/rule_based_detection/debug_block1_detection.py --ticker 025980

# 특정 날짜 확인
python scripts/rule_based_detection/debug_block1_detection.py --ticker 025980 --date 2020-01-15
```

---

### test_seed_detector_2020.py
**목적**: Seed 탐지 테스트 (2020년 데이터)

**특징**:
- 2020년 데이터로 Seed 탐지 테스트
- 검증 및 벤치마킹용

**사용법**:
```bash
python scripts/rule_based_detection/test_seed_detector_2020.py
```

---

## 블록 탐지 시스템

### 블록 정의
- **Block1**: 초기 상승 모멘텀 (거래량 급증 + 이평선 돌파)
- **Block2**: Block1 이후 추가 상승 (가격 레벨업)
- **Block3**: Block2 이후 추가 상승 (추세 지속)
- **Block4**: Block3 이후 최종 상승

### Seed vs Redetection
- **Seed**: 엄격한 조건으로 초기 패턴 탐지
- **Redetection**: 완화된 조건으로 과거 5년간 유사 패턴 탐지

## 참고

- [블록 탐지 시스템 상세 명세](../../docs/specification/BLOCK_DETECTION.md)
- [프리셋 설정](../../presets/README.md)
