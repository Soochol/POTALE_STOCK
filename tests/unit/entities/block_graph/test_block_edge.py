"""
BlockEdge 단위 테스트
"""
import pytest
from src.domain.entities.block_graph import BlockEdge, EdgeType


class TestBlockEdge:
    """BlockEdge 테스트"""

    def test_create_sequential_edge(self):
        """순차적 엣지 생성"""
        edge = BlockEdge(
            from_block_id="block1",
            to_block_id="block2",
            edge_type=EdgeType.SEQUENTIAL
        )

        assert edge.from_block_id == "block1"
        assert edge.to_block_id == "block2"
        assert edge.edge_type == EdgeType.SEQUENTIAL
        assert edge.condition is None
        assert edge.priority == 0

    def test_create_conditional_edge(self):
        """조건부 엣지 생성"""
        edge = BlockEdge(
            from_block_id="block1",
            to_block_id="block2a",
            edge_type=EdgeType.CONDITIONAL,
            condition="current.volume >= 1000000"
        )

        assert edge.is_conditional()
        assert edge.condition == "current.volume >= 1000000"

    def test_create_branching_edge(self):
        """분기 엣지 생성"""
        edge = BlockEdge(
            from_block_id="block1",
            to_block_id="block2a",
            edge_type=EdgeType.BRANCHING,
            priority=1
        )

        assert edge.is_branching()
        assert edge.priority == 1

    def test_create_optional_edge(self):
        """선택적 엣지 생성 (스킵 가능)"""
        edge = BlockEdge(
            from_block_id="block1",
            to_block_id="block3",
            edge_type=EdgeType.OPTIONAL
        )

        assert edge.is_optional()

    def test_conditional_edge_without_condition_fails(self):
        """조건부 엣지에 condition 없으면 실패"""
        with pytest.raises(ValueError, match="condition"):
            BlockEdge(
                from_block_id="block1",
                to_block_id="block2",
                edge_type=EdgeType.CONDITIONAL
                # condition 없음!
            )

    def test_self_loop_fails(self):
        """자기 자신으로의 엣지는 허용되지 않음"""
        with pytest.raises(ValueError, match="자기 자신"):
            BlockEdge(
                from_block_id="block1",
                to_block_id="block1"  # 같은 블록!
            )

    def test_validate_success(self):
        """검증 성공"""
        edge = BlockEdge(
            from_block_id="block1",
            to_block_id="block2"
        )

        errors = edge.validate()
        assert len(errors) == 0

    def test_validate_missing_from_block_id(self):
        """from_block_id 없음 - 검증 실패"""
        # Note: __post_init__에서 먼저 체크하므로 ValueError 발생
        with pytest.raises(ValueError):
            BlockEdge(
                from_block_id="",
                to_block_id="block2"
            )

    def test_validate_missing_to_block_id(self):
        """to_block_id 없음 - 검증 실패"""
        with pytest.raises(ValueError):
            BlockEdge(
                from_block_id="block1",
                to_block_id=""
            )

    def test_edge_priority_sorting(self):
        """우선순위로 정렬 가능"""
        edges = [
            BlockEdge("block1", "block2a", priority=2),
            BlockEdge("block1", "block2b", priority=1),
            BlockEdge("block1", "block2c", priority=3),
        ]

        sorted_edges = sorted(edges, key=lambda e: e.priority)

        assert sorted_edges[0].to_block_id == "block2b"  # priority=1
        assert sorted_edges[1].to_block_id == "block2a"  # priority=2
        assert sorted_edges[2].to_block_id == "block2c"  # priority=3
