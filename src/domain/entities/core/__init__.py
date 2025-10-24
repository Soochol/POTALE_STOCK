"""
Core Domain Entities
기본 도메인 엔티티 (Stock, DetectionResult)
"""
from .stock import Stock
from .detection_result import DetectionResult

__all__ = [
    'Stock',
    'DetectionResult',
]
