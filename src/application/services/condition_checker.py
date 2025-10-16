"""
Condition Checker Service - 조건 검사 서비스
"""
from typing import List
from ...domain.entities.stock import Stock
from ...domain.entities.condition import Condition, Rule, RuleType


class ConditionChecker:
    """조건 검사 서비스"""

    def check(self, condition: Condition, stocks: List[Stock]) -> List[Stock]:
        """
        조건을 만족하는 주식 데이터 필터링

        Args:
            condition: 검사할 조건
            stocks: 주식 데이터 리스트

        Returns:
            조건을 만족하는 주식 데이터 리스트
        """
        if not stocks:
            return []

        result = []

        for stock in stocks:
            if self._check_stock(condition, stock, stocks):
                result.append(stock)

        return result

    def _check_stock(
        self,
        condition: Condition,
        stock: Stock,
        all_stocks: List[Stock]
    ) -> bool:
        """
        특정 주식이 조건을 만족하는지 확인

        Args:
            condition: 조건
            stock: 검사할 주식
            all_stocks: 전체 주식 데이터 (히스토리 참조용)

        Returns:
            조건 만족 여부
        """
        # 모든 규칙을 만족해야 함 (AND 조건)
        for rule in condition.rules:
            if not self._check_rule(rule, stock, all_stocks):
                return False
        return True

    def _check_rule(
        self,
        rule: Rule,
        stock: Stock,
        all_stocks: List[Stock]
    ) -> bool:
        """
        특정 규칙 검사

        Args:
            rule: 규칙
            stock: 주식
            all_stocks: 전체 주식 데이터

        Returns:
            규칙 만족 여부
        """
        if rule.type == RuleType.CROSS_OVER:
            return self._check_cross_over(rule, stock)

        elif rule.type == RuleType.INDICATOR_THRESHOLD:
            return self._check_indicator_threshold(rule, stock)

        elif rule.type == RuleType.VOLUME_INCREASE:
            return self._check_volume_increase(rule, stock)

        elif rule.type == RuleType.PRICE_CHANGE:
            return self._check_price_change(rule, stock, all_stocks)

        return False

    def _check_cross_over(self, rule: Rule, stock: Stock) -> bool:
        """골든크로스/데드크로스 검사"""
        if not hasattr(stock, 'indicators'):
            return False

        indicators = stock.indicators
        indicator1 = rule.parameters.get('indicator1')
        indicator2 = rule.parameters.get('indicator2')

        if indicator1 not in indicators or indicator2 not in indicators:
            return False

        # 현재 값 비교 (단순화된 버전)
        return indicators[indicator1] > indicators[indicator2]

    def _check_indicator_threshold(self, rule: Rule, stock: Stock) -> bool:
        """지표 임계값 검사"""
        if not hasattr(stock, 'indicators'):
            return False

        indicators = stock.indicators
        indicator = rule.parameters.get('indicator')
        condition = rule.parameters.get('condition')
        value = rule.parameters.get('value')

        if indicator not in indicators:
            return False

        indicator_value = indicators[indicator]

        if condition == '>':
            return indicator_value > value
        elif condition == '<':
            return indicator_value < value
        elif condition == '>=':
            return indicator_value >= value
        elif condition == '<=':
            return indicator_value <= value
        elif condition == '==':
            return indicator_value == value

        return False

    def _check_volume_increase(self, rule: Rule, stock: Stock) -> bool:
        """거래량 증가 검사"""
        if not hasattr(stock, 'indicators'):
            return False

        indicators = stock.indicators
        threshold = rule.parameters.get('threshold', 1.5)

        if 'Volume_MA' not in indicators:
            return False

        volume_ma = indicators['Volume_MA']
        return stock.volume > (volume_ma * threshold)

    def _check_price_change(
        self,
        rule: Rule,
        stock: Stock,
        all_stocks: List[Stock]
    ) -> bool:
        """가격 변화율 검사"""
        days = rule.parameters.get('days', 1)
        threshold = rule.parameters.get('threshold', 0.02)

        # 동일 종목의 과거 데이터 찾기
        same_ticker_stocks = [
            s for s in all_stocks
            if s.ticker == stock.ticker and s.date < stock.date
        ]

        if not same_ticker_stocks or len(same_ticker_stocks) < days:
            return False

        # 날짜 기준 정렬
        same_ticker_stocks.sort(key=lambda x: x.date)

        # N일 전 데이터
        past_stock = same_ticker_stocks[-days]

        # 가격 변화율 계산
        if past_stock.close == 0:
            return False

        price_change = (stock.close - past_stock.close) / past_stock.close

        return price_change >= threshold
