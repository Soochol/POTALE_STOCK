"""
Block Detection 테이블에 pattern_id와 detection_type 컬럼 추가

Migration Script for Pattern Re-detection System
"""
from sqlalchemy import text
from src.infrastructure.database.connection import DatabaseConnection


def migrate_add_pattern_columns():
    """Block Detection 테이블에 패턴 관련 컬럼 추가"""
    print("=" * 70)
    print("패턴 재탐지 시스템 - 컬럼 추가 마이그레이션")
    print("=" * 70)

    db = DatabaseConnection("data/database/stock_data.db")

    # ALTER TABLE 쿼리들
    migrations = [
        # Block1Detection
        "ALTER TABLE block1_detection ADD COLUMN pattern_id INTEGER",
        "ALTER TABLE block1_detection ADD COLUMN detection_type VARCHAR(20)",

        # Block2Detection
        "ALTER TABLE block2_detection ADD COLUMN pattern_id INTEGER",
        "ALTER TABLE block2_detection ADD COLUMN detection_type VARCHAR(20)",

        # Block3Detection
        "ALTER TABLE block3_detection ADD COLUMN pattern_id INTEGER",
        "ALTER TABLE block3_detection ADD COLUMN detection_type VARCHAR(20)",
    ]

    print("\n[1] 컬럼 추가 중...")

    with db.engine.connect() as conn:
        for i, migration in enumerate(migrations, 1):
            try:
                conn.execute(text(migration))
                conn.commit()
                table_name = migration.split()[2]  # block1_detection
                column_name = migration.split()[5]  # pattern_id
                print(f"  [{i}/6] [OK] {table_name}.{column_name} 추가 완료")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  [{i}/6] [SKIP] 컬럼이 이미 존재: {migration.split()[2]}.{migration.split()[5]}")
                else:
                    print(f"  [{i}/6] [ERR] {e}")
                    raise

    print("\n[2] 인덱스 생성 중...")

    indexes = [
        "CREATE INDEX IF NOT EXISTS ix_block1_pattern ON block1_detection(pattern_id)",
        "CREATE INDEX IF NOT EXISTS ix_block1_detection_type ON block1_detection(detection_type)",
        "CREATE INDEX IF NOT EXISTS ix_block2_pattern ON block2_detection(pattern_id)",
        "CREATE INDEX IF NOT EXISTS ix_block2_detection_type ON block2_detection(detection_type)",
        "CREATE INDEX IF NOT EXISTS ix_block3_pattern ON block3_detection(pattern_id)",
        "CREATE INDEX IF NOT EXISTS ix_block3_detection_type ON block3_detection(detection_type)",
    ]

    with db.engine.connect() as conn:
        for i, index_sql in enumerate(indexes, 1):
            try:
                conn.execute(text(index_sql))
                conn.commit()
                index_name = index_sql.split()[5]  # ix_block1_pattern
                print(f"  [{i}/6] [OK] {index_name} 인덱스 생성 완료")
            except Exception as e:
                print(f"  [{i}/6] [ERR] {e}")

    print("\n[3] 검증...")
    from sqlalchemy import inspect
    inspector = inspect(db.engine)

    for table_name in ['block1_detection', 'block2_detection', 'block3_detection']:
        columns = [col['name'] for col in inspector.get_columns(table_name)]

        if 'pattern_id' in columns and 'detection_type' in columns:
            print(f"  [OK] {table_name}: pattern_id, detection_type 컬럼 존재")
        else:
            print(f"  [ERR] {table_name}: 컬럼 확인 실패")

    print("\n" + "=" * 70)
    print("마이그레이션 완료!")
    print("=" * 70)


if __name__ == "__main__":
    migrate_add_pattern_columns()
