"""
BlockNode 단위 테스트
"""
import pytest
from src.domain.entities.block_graph import BlockNode


class TestBlockNode:
    """BlockNode 테스트"""

    def test_create_basic_node(self):
        """기본 노드 생성"""
        node = BlockNode(
            block_id="block1",
            block_type=1,
            name="Initial Surge"
        )

        assert node.block_id == "block1"
        assert node.block_type == 1
        assert node.name == "Initial Surge"
        assert node.description == ""
        assert node.entry_conditions == []
        assert node.exit_conditions == []
        assert node.parameters == {}

    def test_create_node_with_conditions(self):
        """조건이 있는 노드 생성"""
        node = BlockNode(
            block_id="block1",
            block_type=1,
            name="Initial Surge",
            entry_conditions=[
                "current.close >= ma(120)",
                "current.volume >= volume_ma(20) * 3"
            ],
            exit_conditions=[
                "current.close < ma(120)"
            ]
        )

        assert len(node.entry_conditions) == 2
        assert len(node.exit_conditions) == 1

    def test_add_entry_condition(self):
        """진입 조건 추가"""
        node = BlockNode(
            block_id="block1",
            block_type=1,
            name="Test"
        )

        node.add_entry_condition("current.close >= 10000")
        assert len(node.entry_conditions) == 1
        assert "current.close >= 10000" in node.entry_conditions

        # 중복 추가 시 무시
        node.add_entry_condition("current.close >= 10000")
        assert len(node.entry_conditions) == 1

    def test_add_exit_condition(self):
        """종료 조건 추가"""
        node = BlockNode(
            block_id="block1",
            block_type=1,
            name="Test"
        )

        node.add_exit_condition("current.close < ma(120)")
        assert len(node.exit_conditions) == 1

    def test_set_and_get_parameter(self):
        """파라미터 설정 및 조회"""
        node = BlockNode(
            block_id="block1",
            block_type=1,
            name="Test"
        )

        node.set_parameter("min_candles", 2)
        node.set_parameter("max_candles", 150)

        assert node.get_parameter("min_candles") == 2
        assert node.get_parameter("max_candles") == 150
        assert node.get_parameter("unknown", 999) == 999

    def test_validate_success(self):
        """검증 성공"""
        node = BlockNode(
            block_id="block1",
            block_type=1,
            name="Test",
            entry_conditions=["current.close >= 10000"]
        )

        errors = node.validate()
        assert len(errors) == 0

    def test_validate_missing_entry_conditions(self):
        """진입 조건 없음 - 검증 실패"""
        node = BlockNode(
            block_id="block1",
            block_type=1,
            name="Test"
        )

        errors = node.validate()
        assert len(errors) > 0
        assert any("entry_condition" in err for err in errors)

    def test_validate_invalid_block_type(self):
        """잘못된 block_type - 검증 실패"""
        with pytest.raises(ValueError, match="block_type"):
            BlockNode(
                block_id="block1",
                block_type=0,  # 0은 허용되지 않음
                name="Test"
            )

    def test_validate_missing_block_id(self):
        """block_id 없음 - 검증 실패"""
        with pytest.raises(ValueError, match="block_id"):
            BlockNode(
                block_id="",
                block_type=1,
                name="Test"
            )
