"""
네이버 금융에서 전체 종목 리스트 가져오기

네이버 금융의 시가총액 페이지에서 모든 상장 종목 코드를 수집합니다.
pykrx를 대체하는 100% 네이버 금융 기반 솔루션입니다.
"""
import requests
from bs4 import BeautifulSoup
import time
from typing import List


def get_naver_ticker_list(market: str = 'KOSPI') -> List[str]:
    """
    네이버 금융 시가총액 페이지에서 종목 리스트 수집

    Args:
        market: 'KOSPI' (sosok=0) 또는 'KOSDAQ' (sosok=1)

    Returns:
        list: 종목 코드 리스트

    Example:
        >>> kospi_tickers = get_naver_ticker_list('KOSPI')
        >>> print(f"KOSPI 종목 수: {len(kospi_tickers)}")
        KOSPI 종목 수: 2387
    """
    sosok = 0 if market.upper() == 'KOSPI' else 1
    base_url = 'https://finance.naver.com/sise/sise_market_sum.naver'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    all_tickers = []
    page = 1

    while True:
        params = {
            'sosok': sosok,
            'page': page
        }

        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=10)

            if response.status_code != 200:
                break

            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')

            # 종목 테이블 찾기
            table = soup.find('table', {'class': 'type_2'})

            if not table:
                break

            # 종목 링크에서 코드 추출
            links = table.find_all('a', href=True)
            page_tickers = []

            for link in links:
                href = link.get('href', '')
                if 'code=' in href:
                    # href: "/item/main.naver?code=005930"
                    ticker = href.split('code=')[1].split('&')[0]
                    if ticker and ticker not in all_tickers:
                        page_tickers.append(ticker)
                        all_tickers.append(ticker)

            if not page_tickers:
                break

            # 다음 페이지
            page += 1

            # 너무 빠른 요청 방지
            time.sleep(0.05)

            # 최대 페이지 제한 (안전장치)
            if page > 100:
                break

        except Exception as e:
            print(f'[Warning] Failed to fetch page {page}: {e}')
            break

    return all_tickers


def get_all_tickers() -> List[str]:
    """
    KOSPI + KOSDAQ 전체 종목 리스트 가져오기

    Returns:
        list: 전체 종목 코드 리스트 (정렬됨)

    Example:
        >>> all_tickers = get_all_tickers()
        >>> print(f"전체 종목 수: {len(all_tickers)}")
        전체 종목 수: 4189
    """
    print("전체 종목 리스트 로딩 중... (네이버 금융)")

    # KOSPI 종목
    print("  KOSPI 수집 중...", end='')
    kospi_tickers = get_naver_ticker_list('KOSPI')
    print(f" {len(kospi_tickers)}개")

    # KOSDAQ 종목
    print("  KOSDAQ 수집 중...", end='')
    kosdaq_tickers = get_naver_ticker_list('KOSDAQ')
    print(f" {len(kosdaq_tickers)}개")

    # 전체 종목 (중복 제거 및 정렬)
    all_tickers = sorted(set(kospi_tickers + kosdaq_tickers))

    print(f"  총 {len(all_tickers)}개 종목 발견")
    print(f"    - KOSPI: {len(kospi_tickers)}개")
    print(f"    - KOSDAQ: {len(kosdaq_tickers)}개")

    return all_tickers


if __name__ == '__main__':
    # 테스트
    tickers = get_all_tickers()
    print(f"\n샘플 종목 10개: {', '.join(tickers[:10])}")
