# 마이그레이션 스크립트

데이터베이스 스키마 및 데이터 마이그레이션 스크립트 모음

## 스크립트 목록

### Preset 관련
- `check_preset_names.py` - 프리셋 이름 확인
- `check_preset_sync.py` - 프리셋 동기화 확인
- `recreate_preset_tables.py` - 프리셋 테이블 재생성

### 파라미터 수정
- `fix_blockN_specific_params.py` - BlockN 특정 파라미터 수정
- `fix_double_block1_prefix.py` - 중복 block1 prefix 수정
- `migrate_add_block1_prefix.py` - block1 prefix 추가
- `migrate_add_blockN_all_params.py` - BlockN 전체 파라미터 추가
- `migrate_rename_block23_params.py` - Block2/3 파라미터 이름 변경
- `migrate_rename_entry_params.py` - Entry 파라미터 이름 변경
- `migrate_reorder_preset_columns.py` - 프리셋 컬럼 순서 재정렬

### 테이블 변경
- `migrate_add_block4_columns.py` - Block4 컬럼 추가
- `migrate_drop_legacy_condition_tables.py` - 레거시 조건 테이블 삭제

## 사용 방법

```bash
# 개별 마이그레이션 실행
python migrations/migrate_add_block4_columns.py

# 프리셋 재생성
python migrations/recreate_preset_tables.py
```

## 주의사항

- 마이그레이션 실행 전 데이터베이스 백업 필수
- 순서대로 실행해야 하는 경우 파일명 순서 참고
- 이미 실행된 마이그레이션 재실행 시 오류 발생 가능
