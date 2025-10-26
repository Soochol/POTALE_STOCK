"""Verify Virtual Block System"""
import sqlite3

conn = sqlite3.connect('data/database/stock_data.db')
cursor = conn.cursor()

print("=" * 80)
print("VIRTUAL BLOCK SYSTEM VERIFICATION")
print("=" * 80)
print()

# Query all blocks for ticker 025980
rows = cursor.execute("""
    SELECT id, block_id, yaml_type, logical_level, pattern_sequence, is_virtual, status, started_at
    FROM dynamic_block_detection
    WHERE ticker='025980'
    ORDER BY id DESC
    LIMIT 10
""").fetchall()

print(f"Found {len(rows)} blocks:\n")
print(f"{'ID':>3} | {'Block':<7} | {'YAML':>4} | {'Level':>5} | {'Seq':>3} | {'Virtual':>7} | {'Status':<16} | {'Started'}")
print("-" * 80)

for row in rows:
    id, block_id, yaml_type, logical_level, pattern_sequence, is_virtual, status, started_at = row
    virtual_str = "YES" if is_virtual == 1 else "NO"
    print(f"{id:>3} | {block_id:<7} | {yaml_type:>4} | {logical_level:>5} | {pattern_sequence:>3} | {virtual_str:>7} | {status:<16} | {started_at}")

print()
print("=" * 80)

# Count virtual blocks
virtual_count = cursor.execute("""
    SELECT COUNT(*) FROM dynamic_block_detection
    WHERE ticker='025980' AND is_virtual=1
""").fetchone()[0]

real_count = cursor.execute("""
    SELECT COUNT(*) FROM dynamic_block_detection
    WHERE ticker='025980' AND is_virtual=0
""").fetchone()[0]

print(f"Virtual blocks: {virtual_count}")
print(f"Real blocks: {real_count}")
print("=" * 80)

conn.close()
