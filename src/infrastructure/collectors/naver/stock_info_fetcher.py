"""
Stock Info Fetcher - 네이버 금융에서 종목 정보 수집
"""
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Optional


async def fetch_stock_info(session: aiohttp.ClientSession, ticker: str) -> Dict[str, str]:
    """
    네이버 금융에서 종목 정보 수집

    Args:
        session: aiohttp 세션
        ticker: 종목 코드

    Returns:
        {'name': str, 'market': str} 또는 기본값
    """
    url = f"https://finance.naver.com/item/main.naver?code={ticker}"

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                return {'name': ticker, 'market': 'UNKNOWN'}

            html = await response.text()
            soup = BeautifulSoup(html, 'lxml')

            # 종목명 추출
            name = ticker  # 기본값
            name_tag = soup.select_one('.wrap_company h2 a')
            if name_tag:
                name = name_tag.text.strip()

            # 시장구분 추출 (KOSPI/KOSDAQ)
            market = 'UNKNOWN'
            market_tag = soup.select_one('.wrap_company em.market')
            if market_tag:
                market_text = market_tag.text.strip()
                if 'KOSPI' in market_text:
                    market = 'KOSPI'
                elif 'KOSDAQ' in market_text:
                    market = 'KOSDAQ'
                elif 'KONEX' in market_text:
                    market = 'KONEX'

            return {
                'name': name,
                'market': market
            }

    except Exception as e:
        # 실패 시 기본값 반환
        return {
            'name': ticker,
            'market': 'UNKNOWN'
        }


def fetch_stock_info_sync(ticker: str) -> Dict[str, str]:
    """
    동기 버전: 네이버 금융에서 종목 정보 수집 (fallback용)

    Args:
        ticker: 종목 코드

    Returns:
        {'name': str, 'market': str}
    """
    import requests

    url = f"https://finance.naver.com/item/main.naver?code={ticker}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {'name': ticker, 'market': 'UNKNOWN'}

        soup = BeautifulSoup(response.text, 'lxml')

        # 종목명 추출
        name = ticker
        name_tag = soup.select_one('.wrap_company h2 a')
        if name_tag:
            name = name_tag.text.strip()

        # 시장구분 추출
        market = 'UNKNOWN'
        market_tag = soup.select_one('.wrap_company em.market')
        if market_tag:
            market_text = market_tag.text.strip()
            if 'KOSPI' in market_text:
                market = 'KOSPI'
            elif 'KOSDAQ' in market_text:
                market = 'KOSDAQ'
            elif 'KONEX' in market_text:
                market = 'KONEX'

        return {
            'name': name,
            'market': market
        }

    except Exception:
        return {
            'name': ticker,
            'market': 'UNKNOWN'
        }
