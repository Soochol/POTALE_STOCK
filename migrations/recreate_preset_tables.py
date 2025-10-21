"""
Preset 테이블 재생성 스크립트
DB 스키마 변경 후 테이블을 삭제하고 재생성
"""
import sys
import os

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.models import Base

def main():
    db = DatabaseConnection('data/database/stock_data.db')

    print("=" * 80)
    print("Preset 테이블 재생성")
    print("=" * 80)
    print()

    print("[1단계] 기존 Preset 테이블 삭제...")
    try:
        from sqlalchemy import MetaData
        metadata = MetaData()
        metadata.reflect(bind=db.engine)

        # Preset 테이블만 삭제
        for table_name in ['seed_condition_preset', 'redetection_condition_preset']:
            if table_name in metadata.tables:
                metadata.tables[table_name].drop(db.engine)
                print(f"  ✓ {table_name} 테이블 삭제 완료")
        print()
    except Exception as e:
        print(f"  경고: 테이블 삭제 중 오류 (무시 가능): {e}")
        print()

    print("[2단계] 새로운 스키마로 Preset 테이블 생성...")
    try:
        # Preset 테이블만 생성
        from src.infrastructure.database.models.presets import SeedConditionPreset, RedetectionConditionPreset

        Base.metadata.create_all(
            bind=db.engine,
            tables=[SeedConditionPreset.__table__, RedetectionConditionPreset.__table__]
        )
        print("  ✓ seed_condition_preset 테이블 생성 완료")
        print("  ✓ redetection_condition_preset 테이블 생성 완료")
        print()
    except Exception as e:
        print(f"  ✗ 오류: {e}")
        return 1

    print("=" * 80)
    print("✓ Preset 테이블 재생성 완료!")
    print("=" * 80)
    print()
    print("다음 단계: python update_presets_from_yaml.py 실행하여 YAML 데이터 로드")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
