"""
Three Line Break Chart Calculator - 삼선전환도 계산 서비스
"""
from typing import List, Tuple
from dataclasses import dataclass
from datetime import date


@dataclass
class ThreeLineBreakBar:
    """삼선전환도 바 (라인)"""
    date: date
    high: float
    low: float
    direction: str  # "up" (양봉) or "down" (음봉)

    @property
    def is_up(self) -> bool:
        return self.direction == "up"

    @property
    def is_down(self) -> bool:
        return self.direction == "down"


class ThreeLineBreakCalculator:
    """
    삼선전환도 계산기

    Three Line Break Chart는 시간을 무시하고 가격 변화만 추적합니다.
    - 상승 라인이 3개 연속 후 하락 라인이 나오면 "음전환" (첫 음봉)
    - 하락 라인이 3개 연속 후 상승 라인이 나오면 "양전환" (첫 양봉)

    알고리즘:
    1. 첫 번째 바: 종가 > 시가면 상승, 반대면 하락
    2. 이후:
       - 종가가 직전 라인의 high를 돌파하면 새 상승 라인 생성
       - 종가가 직전 라인의 low를 하향 돌파하면 새 하락 라인 생성
       - 반전 조건: 최근 3개 라인의 최고/최저를 돌파해야 함
    """

    def __init__(self, line_count: int = 3):
        """
        Args:
            line_count: 반전 기준 라인 수 (기본 3)
        """
        self.line_count = line_count

    def calculate(
        self,
        dates: List[date],
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float]
    ) -> List[ThreeLineBreakBar]:
        """
        삼선전환도 계산

        Args:
            dates: 날짜 리스트
            opens: 시가 리스트
            highs: 고가 리스트
            lows: 저가 리스트
            closes: 종가 리스트

        Returns:
            삼선전환도 바 리스트
        """
        if not dates or len(dates) != len(closes):
            return []

        bars: List[ThreeLineBreakBar] = []

        # 첫 번째 바 생성
        first_direction = "up" if closes[0] >= opens[0] else "down"
        first_bar = ThreeLineBreakBar(
            date=dates[0],
            high=max(opens[0], closes[0]),
            low=min(opens[0], closes[0]),
            direction=first_direction
        )
        bars.append(first_bar)

        # 이후 바 계산
        for i in range(1, len(dates)):
            close = closes[i]
            last_bar = bars[-1]

            # 같은 방향으로 계속 진행하는 경우
            if last_bar.is_up and close > last_bar.high:
                # 상승 라인 연장
                new_bar = ThreeLineBreakBar(
                    date=dates[i],
                    high=close,
                    low=last_bar.high,
                    direction="up"
                )
                bars.append(new_bar)

            elif last_bar.is_down and close < last_bar.low:
                # 하락 라인 연장
                new_bar = ThreeLineBreakBar(
                    date=dates[i],
                    high=last_bar.low,
                    low=close,
                    direction="down"
                )
                bars.append(new_bar)

            # 반전 확인
            else:
                reversal_bar = self._check_reversal(bars, dates[i], close)
                if reversal_bar:
                    bars.append(reversal_bar)

        return bars

    def _check_reversal(
        self,
        bars: List[ThreeLineBreakBar],
        current_date: date,
        close: float
    ) -> Tuple[ThreeLineBreakBar, None]:
        """
        반전 조건 확인

        Args:
            bars: 기존 바 리스트
            current_date: 현재 날짜
            close: 현재 종가

        Returns:
            새 반전 바 또는 None
        """
        if len(bars) < self.line_count:
            # 라인이 충분하지 않으면 단순 반전
            last_bar = bars[-1]
            if last_bar.is_up and close < last_bar.low:
                return ThreeLineBreakBar(
                    date=current_date,
                    high=last_bar.low,
                    low=close,
                    direction="down"
                )
            elif last_bar.is_down and close > last_bar.high:
                return ThreeLineBreakBar(
                    date=current_date,
                    high=close,
                    low=last_bar.high,
                    direction="up"
                )
            return None

        # 최근 N개 라인 추출
        recent_bars = bars[-self.line_count:]
        last_bar = bars[-1]

        # 상승 추세에서 하락 반전 체크
        if last_bar.is_up:
            # 최근 3개 라인의 최저가
            lowest = min(bar.low for bar in recent_bars)
            if close < lowest:
                # 하락 반전
                return ThreeLineBreakBar(
                    date=current_date,
                    high=lowest,
                    low=close,
                    direction="down"
                )

        # 하락 추세에서 상승 반전 체크
        elif last_bar.is_down:
            # 최근 3개 라인의 최고가
            highest = max(bar.high for bar in recent_bars)
            if close > highest:
                # 상승 반전
                return ThreeLineBreakBar(
                    date=current_date,
                    high=close,
                    low=highest,
                    direction="up"
                )

        return None

    def detect_first_down_bar(
        self,
        bars: List[ThreeLineBreakBar],
        from_date: date
    ) -> Tuple[date, None]:
        """
        특정 날짜 이후 첫 번째 음봉(하락) 발생 날짜 찾기

        Args:
            bars: 삼선전환도 바 리스트
            from_date: 검색 시작 날짜

        Returns:
            첫 번째 음봉 발생 날짜 또는 None
        """
        prev_bar = None
        for bar in bars:
            if bar.date >= from_date:
                # 이전이 양봉이고 현재가 음봉이면 반전
                if prev_bar and prev_bar.is_up and bar.is_down:
                    return bar.date
            prev_bar = bar

        return None
