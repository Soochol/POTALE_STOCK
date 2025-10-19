# Documentation

주식 패턴 탐지 시스템 문서 모음

## 📁 문서 구조

### 📐 [specification/](specification/) - 기능 명세서
시스템 기능과 비즈니스 로직 명세

- **[BLOCK_DETECTION.md](specification/BLOCK_DETECTION.md)** - Block1/2/3/4 탐지 시스템 완전 가이드
- **[BULK_COLLECTION_DESIGN.md](specification/BULK_COLLECTION_DESIGN.md)** - 대량 데이터 수집 설계
- **[COLLECTOR_FUNDAMENTAL_SOLUTION.md](specification/COLLECTOR_FUNDAMENTAL_SOLUTION.md)** - 컬렉터 기본 솔루션
- **[STREAMLIT_GUI_PLAN.md](specification/STREAMLIT_GUI_PLAN.md)** - GUI 계획서
- **[INTEGRATED_DETECTION_SUMMARY.md](specification/INTEGRATED_DETECTION_SUMMARY.md)** - 통합 탐지 시스템 요약

### 🏗️ [architecture/](architecture/) - 아키텍처 설계
시스템 구조와 데이터베이스 설계

- **[STRUCTURE.md](architecture/STRUCTURE.md)** - 전체 시스템 구조
- **[PROJECT_STRUCTURE.md](architecture/PROJECT_STRUCTURE.md)** - 프로젝트 파일 구조
- **[DATABASE_DESIGN.md](architecture/DATABASE_DESIGN.md)** - 데이터베이스 스키마 설계

### 🔨 [implementation/](implementation/) - 구현 계획 및 기록
개발 로드맵과 구현 내역

- **[IMPLEMENTATION_ROADMAP.md](implementation/IMPLEMENTATION_ROADMAP.md)** - 개발 로드맵
- **[IMPLEMENTATION_SUMMARY.md](implementation/IMPLEMENTATION_SUMMARY.md)** - 구현 요약
- **[REFACTORING_TODO.md](implementation/REFACTORING_TODO.md)** - 리팩토링 TODO
- **[NEXT_SESSION_TODO.md](implementation/NEXT_SESSION_TODO.md)** - 다음 세션 작업 목록

### 📖 [guides/](guides/) - 운영 가이드
성능 최적화, 유지보수 가이드

- **[PERFORMANCE_OPTIMIZATION.md](guides/PERFORMANCE_OPTIMIZATION.md)** - 성능 최적화 가이드
- **[DATABASE_CLEANUP_GUIDE.md](guides/DATABASE_CLEANUP_GUIDE.md)** - 데이터베이스 정리 가이드

### 🔍 [analysis/](analysis/) - 분석 문서
코드 분석, 개선 제안

- **[UNUSED_TABLES_ANALYSIS.md](analysis/UNUSED_TABLES_ANALYSIS.md)** - 미사용 테이블 분석
- **[PARAMETER_NAMING_IMPROVEMENT.md](analysis/PARAMETER_NAMING_IMPROVEMENT.md)** - 파라미터 네이밍 개선

---

## 🎯 빠른 시작

### 시스템 이해하기
1. **[BLOCK_DETECTION.md](specification/BLOCK_DETECTION.md)** - 핵심 기능 이해
2. **[STRUCTURE.md](architecture/STRUCTURE.md)** - 전체 구조 파악
3. **[DATABASE_DESIGN.md](architecture/DATABASE_DESIGN.md)** - 데이터 모델 이해

### 개발하기
1. **[PROJECT_STRUCTURE.md](architecture/PROJECT_STRUCTURE.md)** - 파일 구조 확인
2. **[IMPLEMENTATION_ROADMAP.md](implementation/IMPLEMENTATION_ROADMAP.md)** - 개발 방향 확인
3. **[REFACTORING_TODO.md](implementation/REFACTORING_TODO.md)** - 리팩토링 작업 확인

### 운영하기
1. **[PERFORMANCE_OPTIMIZATION.md](guides/PERFORMANCE_OPTIMIZATION.md)** - 성능 최적화
2. **[DATABASE_CLEANUP_GUIDE.md](guides/DATABASE_CLEANUP_GUIDE.md)** - DB 정리

---

## 📝 최근 업데이트

### 2025-10-19
- ✅ **BaseEntryCondition 조합 패턴 리팩토링 완료**
  - 코드 감소: 385 → 150 lines (-61%)
  - 중복 제거: 44개 → 11개 필드 선언
  - Single Source of Truth 달성
  - [BLOCK_DETECTION.md](specification/BLOCK_DETECTION.md) Phase 2 섹션 업데이트

### 2025-10-18
- ✅ **Block2/3/4 조건 독립성 구조 구현**
  - 의존성 제거, 각 블록 독립 조건값 설정 가능

---

## 🤝 문서 작성 가이드

- **specification/**: 기능 명세, 요구사항, 설계 문서
- **architecture/**: 시스템 구조, 데이터 모델, 기술 스택
- **implementation/**: 개발 계획, TODO, 구현 내역
- **guides/**: How-to 가이드, 운영 매뉴얼
- **analysis/**: 분석 보고서, 개선 제안
