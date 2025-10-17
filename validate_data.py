"""
수집된 데이터 검증 스크립트

사용법:
    python validate_data.py
"""

import sqlite3
from pathlib import Path

db_path = Path('data/database/stock_data.db')

if not db_path.exists():
    print(f"[ERROR] Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("Stock Data Validation Report")
print("=" * 80)

# 1. 기본 통계
print("\n[1] Basic Statistics")
print("-" * 80)

cursor.execute("SELECT COUNT(*) FROM stock_info")
stock_count = cursor.fetchone()[0]
print(f"Stock Info: {stock_count} stocks")

cursor.execute("SELECT COUNT(*) FROM stock_price")
price_count = cursor.fetchone()[0]
print(f"Stock Price: {price_count:,} records")

cursor.execute("SELECT COUNT(*) FROM investor_trading")
investor_count = cursor.fetchone()[0]
print(f"Investor Trading: {investor_count:,} records")

cursor.execute("SELECT COUNT(*) FROM market_data")
market_count = cursor.fetchone()[0]
print(f"Market Data: {market_count:,} records")

# 2. 날짜 범위
print("\n[2] Date Range")
print("-" * 80)

cursor.execute("""
    SELECT
        MIN(date) as first_date,
        MAX(date) as last_date,
        COUNT(DISTINCT date) as trading_days
    FROM stock_price
""")
row = cursor.fetchone()
if row and row[0]:
    print(f"First Date: {row[0]}")
    print(f"Last Date: {row[1]}")
    print(f"Trading Days: {row[2]}")
else:
    print("No price data available")

# 3. 종목별 통계
print("\n[3] Per-Ticker Statistics")
print("-" * 80)

cursor.execute("""
    SELECT
        sp.ticker,
        si.name,
        COUNT(sp.id) as price_count,
        MIN(sp.date) as first_date,
        MAX(sp.date) as last_date
    FROM stock_price sp
    LEFT JOIN stock_info si ON sp.ticker = si.ticker
    GROUP BY sp.ticker
    ORDER BY sp.ticker
""")

print(f"{'Ticker':<10} {'Name':<20} {'Records':>10} {'First Date':<12} {'Last Date':<12}")
print("-" * 80)
for row in cursor.fetchall():
    ticker, name, count, first, last = row
    name = (name or 'N/A')[:18]
    print(f"{ticker:<10} {name:<20} {count:>10} {first:<12} {last:<12}")

# 4. 하이브리드 데이터 검증 (수정주가)
print("\n[4] Hybrid Data Validation (Adjusted Price)")
print("-" * 80)

cursor.execute("""
    SELECT
        date,
        close as adj_close,
        raw_close,
        ROUND(adjustment_ratio, 4) as adj_ratio,
        volume as adj_volume,
        raw_volume
    FROM stock_price
    WHERE ticker = '005930'
    ORDER BY date DESC
    LIMIT 5
""")

print(f"{'Date':<12} {'Adj Close':>10} {'Raw Close':>10} {'Ratio':>8} {'Adj Vol':>12} {'Raw Vol':>12}")
print("-" * 80)
for row in cursor.fetchall():
    date_val, adj_close, raw_close, ratio, adj_vol, raw_vol = row
    print(f"{date_val:<12} {adj_close:>10.0f} {raw_close:>10.0f} {ratio:>8} {adj_vol:>12,} {raw_vol:>12,}")

# 5. 투자자 거래 데이터
print("\n[5] Investor Trading Data")
print("-" * 80)

cursor.execute("""
    SELECT
        ticker,
        date,
        institution_net_buy,
        foreign_net_buy,
        individual_net_buy
    FROM investor_trading
    ORDER BY date DESC
    LIMIT 10
""")

rows = cursor.fetchall()
if rows:
    print(f"{'Ticker':<10} {'Date':<12} {'Institution':>15} {'Foreign':>15} {'Individual':>15}")
    print("-" * 80)
    for row in rows:
        ticker, date, inst, foreign, indiv = row
        print(f"{ticker:<10} {date:<12} {inst:>15,} {foreign:>15,} {indiv:>15,}")
else:
    print("No investor trading data available")

# 6. 데이터 품질 체크
print("\n[6] Data Quality Checks")
print("-" * 80)

# NULL 체크
cursor.execute("""
    SELECT COUNT(*)
    FROM stock_price
    WHERE close IS NULL OR volume IS NULL
""")
null_count = cursor.fetchone()[0]
print(f"Records with NULL (close/volume): {null_count}")

# 이상값 체크 (0원 종가)
cursor.execute("""
    SELECT COUNT(*)
    FROM stock_price
    WHERE close = 0
""")
zero_count = cursor.fetchone()[0]
print(f"Records with zero close price: {zero_count}")

# 중복 체크
cursor.execute("""
    SELECT ticker, date, COUNT(*) as dup_count
    FROM stock_price
    GROUP BY ticker, date
    HAVING COUNT(*) > 1
""")
duplicates = cursor.fetchall()
if duplicates:
    print(f"Duplicate records found: {len(duplicates)}")
    for dup in duplicates[:5]:
        print(f"  - {dup[0]} on {dup[1]}: {dup[2]} records")
else:
    print("No duplicates found")

print("\n" + "=" * 80)
print("Validation Complete")
print("=" * 80)

conn.close()
