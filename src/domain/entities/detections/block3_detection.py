"""
Block3 Detection Entity - 블록3 탐지 결과 엔티티
"""
from dataclasses import dataclass
import uuid

from .base_detection import BaseBlockDetection


@dataclass
class Block3Detection(BaseBlockDetection):
    """블록3 탐지 결과 (BaseBlockDetection 상속)"""

    block3_id: str = ""  # 블록3 고유 ID (UUID)

    def __post_init__(self):
        """UUID 생성 및 유효성 검사"""
        # UUID 생성
        if not self.block3_id:
            self.block3_id = str(uuid.uuid4())

        # block_id는 block3_id로 설정 (호환성)
        self.block_id = self.block3_id

        # 부모 클래스 유효성 검사
        super().__post_init__()

    @property
    def prev_block2_id(self):
        """호환성을 위한 별칭"""
        return self.prev_block_id

    @prev_block2_id.setter
    def prev_block2_id(self, value):
        self.prev_block_id = value

    @property
    def prev_block2_peak_price(self):
        """호환성을 위한 별칭"""
        return self.prev_block_peak_price

    @prev_block2_peak_price.setter
    def prev_block2_peak_price(self, value):
        self.prev_block_peak_price = value

    @property
    def prev_block2_peak_volume(self):
        """호환성을 위한 별칭"""
        return self.prev_block_peak_volume

    @prev_block2_peak_volume.setter
    def prev_block2_peak_volume(self, value):
        self.prev_block_peak_volume = value

    def _get_block_name(self) -> str:
        return "Block3"
