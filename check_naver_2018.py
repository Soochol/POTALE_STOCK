"""
네이버 금융에서 2018년 3월 7일 데이터 확인
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

ticker = '025980'
url = f'https://finance.naver.com/item/sise_day.naver'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print('네이버 금융에서 아난티(025980) - 2018.03.07 데이터 확인')
print('='*70)

target_date = '2018.03.07'
found = False

# 2018년 3월은 약 1900일 전 = 약 380페이지 (페이지당 5일)
for page in range(370, 400):
    try:
        params = {'code': ticker, 'page': page}
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code != 200:
            continue

        dfs = pd.read_html(response.text, encoding='euc-kr')

        if not dfs or len(dfs) == 0:
            continue

        df = dfs[0]
        df = df.dropna(subset=[df.columns[0]])

        # 날짜 컬럼 확인
        for idx, row in df.iterrows():
            date_str = str(row.iloc[0]).strip()

            if target_date in date_str:
                print(f'\n페이지 {page}에서 발견!')
                print('-'*70)
                print(f'날짜:     {date_str}')
                print(f'종가:     {row.iloc[1]}원')
                print(f'전일비:   {row.iloc[2]}')
                print(f'시가:     {row.iloc[3]}원')
                print(f'고가:     {row.iloc[4]}원')
                print(f'저가:     {row.iloc[5]}원')
                print(f'거래량:   {row.iloc[6]}주')

                # pykrx 데이터와 비교
                print('\n[pykrx 데이터와 비교]')
                print(f'pykrx 종가:   6,230원')
                print(f'pykrx 거래량: 1,118,370주')
                print(f'pykrx 시가:   7,000원')
                print(f'pykrx 고가:   7,460원')
                print(f'pykrx 저가:   6,139원')

                found = True
                break

        if found:
            break

        if page % 5 == 0:
            print(f'페이지 {page} 확인 중...')

        time.sleep(0.1)

    except Exception as e:
        print(f'페이지 {page} 오류: {e}')
        continue

if not found:
    print('\n해당 날짜를 찾지 못했습니다.')
    print('더 넓은 범위를 검색하거나 다른 방법이 필요합니다.')

print('\n' + '='*70)
