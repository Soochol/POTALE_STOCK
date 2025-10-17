"""
아난티(025980) 주식 데이터 추출 스크립트

사용법:
    python extract_ananti.py
"""

from pykrx import stock
from datetime import date, datetime, timedelta
import pandas as pd

ticker = "025980"
company_name = "아난티"

print("=" * 80)
print(f"{company_name} ({ticker}) 주식 데이터 추출")
print("=" * 80)

# 기간 설정
fromdate = date(2020, 1, 1)
todate = date.today()

print(f"\n기간: {fromdate} ~ {todate}")

# 1. OHLCV 데이터 수집
print("\n[1] OHLCV 데이터 수집 중...")
try:
    df_ohlcv = stock.get_market_ohlcv_by_date(
        fromdate=fromdate.strftime("%Y%m%d"),
        todate=todate.strftime("%Y%m%d"),
        ticker=ticker
    )

    if df_ohlcv.empty:
        print(f"  [경고] OHLCV 데이터가 없습니다.")
    else:
        print(f"  [성공] {len(df_ohlcv)}개 레코드 수집")
        print(f"\n  최근 5일 데이터:")
        print(df_ohlcv.tail())

        # CSV 저장
        csv_path = f"data/{ticker}_{company_name}_ohlcv.csv"
        df_ohlcv.to_csv(csv_path, encoding='utf-8-sig')
        print(f"\n  저장: {csv_path}")

except Exception as e:
    print(f"  [오류] {e}")
    df_ohlcv = pd.DataFrame()

# 2. 시가총액, PER, PBR 등 펀더멘털 데이터
print("\n[2] 펀더멘털 데이터 수집 중...")
try:
    df_fundamental = stock.get_market_fundamental_by_date(
        fromdate=fromdate.strftime("%Y%m%d"),
        todate=todate.strftime("%Y%m%d"),
        ticker=ticker
    )

    if df_fundamental.empty:
        print(f"  [경고] 펀더멘털 데이터가 없습니다.")
    else:
        print(f"  [성공] {len(df_fundamental)}개 레코드 수집")
        print(f"\n  최근 5일 데이터:")
        print(df_fundamental.tail())

        # CSV 저장
        csv_path = f"data/{ticker}_{company_name}_fundamental.csv"
        df_fundamental.to_csv(csv_path, encoding='utf-8-sig')
        print(f"\n  저장: {csv_path}")

except Exception as e:
    print(f"  [오류] {e}")
    df_fundamental = pd.DataFrame()

# 3. 투자자별 거래 데이터 (최근 1년)
print("\n[3] 투자자별 거래 데이터 수집 중 (최근 1년)...")
try:
    # pykrx는 투자자별 거래를 전체 시장 기준으로만 제공하므로
    # 개별 종목은 네이버 금융에서 수집 필요
    one_year_ago = todate - timedelta(days=365)

    df_investor = stock.get_market_trading_value_by_date(
        fromdate=one_year_ago.strftime("%Y%m%d"),
        todate=todate.strftime("%Y%m%d"),
        ticker=ticker
    )

    if df_investor.empty:
        print(f"  [경고] 투자자 거래 데이터가 없습니다.")
    else:
        print(f"  [성공] {len(df_investor)}개 레코드 수집")
        print(f"\n  최근 5일 데이터:")
        print(df_investor.tail())

        # CSV 저장
        csv_path = f"data/{ticker}_{company_name}_investor.csv"
        df_investor.to_csv(csv_path, encoding='utf-8-sig')
        print(f"\n  저장: {csv_path}")

except Exception as e:
    print(f"  [오류] {e}")
    df_investor = pd.DataFrame()

# 4. 통합 리포트
print("\n" + "=" * 80)
print("데이터 수집 완료")
print("=" * 80)

if not df_ohlcv.empty:
    print(f"\n[통계]")
    print(f"  기간: {df_ohlcv.index[0]} ~ {df_ohlcv.index[-1]}")
    print(f"  거래일 수: {len(df_ohlcv)}일")
    print(f"  최고가: {df_ohlcv['고가'].max():,.0f}원 ({df_ohlcv['고가'].idxmax()})")
    print(f"  최저가: {df_ohlcv['저가'].min():,.0f}원 ({df_ohlcv['저가'].idxmin()})")
    print(f"  현재가: {df_ohlcv['종가'].iloc[-1]:,.0f}원")
    print(f"  평균 거래량: {df_ohlcv['거래량'].mean():,.0f}주")
    print(f"  최대 거래량: {df_ohlcv['거래량'].max():,.0f}주 ({df_ohlcv['거래량'].idxmax()})")

    # 수익률 계산
    first_close = df_ohlcv['종가'].iloc[0]
    last_close = df_ohlcv['종가'].iloc[-1]
    total_return = ((last_close - first_close) / first_close) * 100
    print(f"\n  전체 수익률: {total_return:+.2f}%")

    # 연도별 수익률
    print(f"\n[연도별 수익률]")
    df_ohlcv['연도'] = pd.to_datetime(df_ohlcv.index).year
    for year in sorted(df_ohlcv['연도'].unique()):
        year_data = df_ohlcv[df_ohlcv['연도'] == year]
        if len(year_data) > 0:
            year_first = year_data['종가'].iloc[0]
            year_last = year_data['종가'].iloc[-1]
            year_return = ((year_last - year_first) / year_first) * 100
            print(f"  {year}년: {year_return:+.2f}%")

print("\n" + "=" * 80)
print("생성된 파일:")
print(f"  - data/{ticker}_{company_name}_ohlcv.csv")
print(f"  - data/{ticker}_{company_name}_fundamental.csv")
print(f"  - data/{ticker}_{company_name}_investor.csv")
print("=" * 80)
