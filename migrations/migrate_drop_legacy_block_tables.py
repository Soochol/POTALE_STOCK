"""
Migration: Drop Legacy Block Detection Tables

레거시 블록 테이블 삭제 (block1~6_detection, block_pattern)
다이나믹 시스템으로 완전 전환
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "database" / "stock_data.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n=== Drop Legacy Block Detection Tables ===\n")

    # 1. Drop block_pattern (외래키 때문에 먼저 삭제)
    print("1. Dropping block_pattern table...")
    try:
        cursor.execute("DROP TABLE IF EXISTS block_pattern")
        print("   [OK] block_pattern dropped")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # 2. Drop block1~6_detection tables
    for i in range(1, 7):
        table_name = f"block{i}_detection"
        print(f"{i+1}. Dropping {table_name} table...")
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            print(f"   [OK] {table_name} dropped")
        except Exception as e:
            print(f"   [ERROR] {e}")

    conn.commit()

    # 3. Verify remaining tables
    print("\n=== Remaining Tables ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    for table in tables:
        print(f"   - {table[0]}")

    print(f"\n[OK] Total {len(tables)} tables remaining")

    conn.close()
    print("\n[SUCCESS] Migration completed!\n")

if __name__ == "__main__":
    migrate()
