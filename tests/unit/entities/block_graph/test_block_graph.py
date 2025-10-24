"""
BlockGraph 단위 테스트
"""
import pytest
from src.domain.entities.block_graph import BlockGraph, BlockNode, BlockEdge, EdgeType


class TestBlockGraph:
    """BlockGraph 테스트"""

    def test_create_empty_graph(self):
        """빈 그래프 생성"""
        graph = BlockGraph()

        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
        assert graph.root_node_id is None

    def test_add_node(self):
        """노드 추가"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        graph.add_node(node1)

        assert len(graph.nodes) == 1
        assert graph.root_node_id == "block1"

    def test_add_duplicate_node_fails(self):
        """중복 노드 추가 실패"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        graph.add_node(node1)

        # 같은 ID로 다시 추가
        node1_dup = BlockNode("block1", 1, "Block 1 Duplicate", entry_conditions=["true"])

        with pytest.raises(ValueError, match="이미 존재"):
            graph.add_node(node1_dup)

    def test_add_edge(self):
        """엣지 추가"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        node2 = BlockNode("block2", 2, "Block 2", entry_conditions=["true"])

        graph.add_node(node1)
        graph.add_node(node2)

        edge = BlockEdge("block1", "block2")
        graph.add_edge(edge)

        assert len(graph.edges) == 1

    def test_add_edge_with_missing_node_fails(self):
        """존재하지 않는 노드로 엣지 추가 실패"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        graph.add_node(node1)

        # block2는 존재하지 않음
        edge = BlockEdge("block1", "block2")

        with pytest.raises(ValueError, match="알 수 없는 블록 ID"):
            graph.add_edge(edge)

    def test_get_children(self):
        """자식 블록 조회"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        node2 = BlockNode("block2", 2, "Block 2", entry_conditions=["true"])
        node3 = BlockNode("block3", 3, "Block 3", entry_conditions=["true"])

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        graph.add_edge(BlockEdge("block1", "block2", priority=2))
        graph.add_edge(BlockEdge("block1", "block3", priority=1))

        children = graph.get_children("block1")

        # 우선순위로 정렬되어야 함
        assert len(children) == 2
        assert children[0].block_id == "block3"  # priority=1
        assert children[1].block_id == "block2"  # priority=2

    def test_get_parents(self):
        """부모 블록 조회"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        node2a = BlockNode("block2a", 2, "Block 2A", entry_conditions=["true"])
        node2b = BlockNode("block2b", 2, "Block 2B", entry_conditions=["true"])
        node3 = BlockNode("block3", 3, "Block 3", entry_conditions=["true"])

        graph.add_node(node1)
        graph.add_node(node2a)
        graph.add_node(node2b)
        graph.add_node(node3)

        # 다중 부모: block2a, block2b 둘 다 block3으로 전이
        graph.add_edge(BlockEdge("block2a", "block3"))
        graph.add_edge(BlockEdge("block2b", "block3"))

        parents = graph.get_parents("block3")

        assert len(parents) == 2
        assert any(p.block_id == "block2a" for p in parents)
        assert any(p.block_id == "block2b" for p in parents)

    def test_branching_from_single_block(self):
        """분기: 하나의 블록에서 여러 블록으로"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        node2a = BlockNode("block2a", 2, "Block 2A", entry_conditions=["true"])
        node2b = BlockNode("block2b", 2, "Block 2B", entry_conditions=["true"])

        graph.add_node(node1)
        graph.add_node(node2a)
        graph.add_node(node2b)

        # Block1에서 Block2A, Block2B로 분기
        graph.add_edge(BlockEdge("block1", "block2a", edge_type=EdgeType.BRANCHING, priority=1))
        graph.add_edge(BlockEdge("block1", "block2b", edge_type=EdgeType.BRANCHING, priority=2))

        children = graph.get_children("block1")

        assert len(children) == 2
        assert children[0].block_id == "block2a"
        assert children[1].block_id == "block2b"

    def test_skip_intermediate_block(self):
        """스킵: Block1 → Block3 (Block2 건너뛰기)"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        node2 = BlockNode("block2", 2, "Block 2", entry_conditions=["true"])
        node3 = BlockNode("block3", 3, "Block 3", entry_conditions=["true"])

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        # Block1 → Block2 (정상)
        graph.add_edge(BlockEdge("block1", "block2"))
        # Block1 → Block3 (스킵)
        graph.add_edge(BlockEdge("block1", "block3", edge_type=EdgeType.OPTIONAL))

        children = graph.get_children("block1")

        assert len(children) == 2
        assert any(c.block_id == "block2" for c in children)
        assert any(c.block_id == "block3" for c in children)

    def test_cycle_detection(self):
        """순환 감지: Block1 → Block2 → Block1 (불가능)"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        node2 = BlockNode("block2", 2, "Block 2", entry_conditions=["true"])

        graph.add_node(node1)
        graph.add_node(node2)

        graph.add_edge(BlockEdge("block1", "block2"))

        # Block2 → Block1 엣지 추가 시 순환 발생
        edge_cycle = BlockEdge("block2", "block1")

        with pytest.raises(ValueError, match="순환"):
            graph.add_edge(edge_cycle)

    def test_topological_sort(self):
        """위상 정렬"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        node2 = BlockNode("block2", 2, "Block 2", entry_conditions=["true"])
        node3 = BlockNode("block3", 3, "Block 3", entry_conditions=["true"])

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        graph.add_edge(BlockEdge("block1", "block2"))
        graph.add_edge(BlockEdge("block2", "block3"))

        sorted_ids = graph.topological_sort()

        # block1이 먼저, block3이 마지막
        assert sorted_ids.index("block1") < sorted_ids.index("block2")
        assert sorted_ids.index("block2") < sorted_ids.index("block3")

    def test_get_all_paths(self):
        """모든 경로 찾기"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        node2 = BlockNode("block2", 2, "Block 2", entry_conditions=["true"])
        node3 = BlockNode("block3", 3, "Block 3", entry_conditions=["true"])

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        # 2개의 경로 생성:
        # 경로 1: block1 → block2 → block3
        # 경로 2: block1 → block3 (스킵)
        graph.add_edge(BlockEdge("block1", "block2"))
        graph.add_edge(BlockEdge("block2", "block3"))
        graph.add_edge(BlockEdge("block1", "block3"))

        paths = graph.get_all_paths("block1", "block3")

        assert len(paths) == 2
        # 경로 1: ["block1", "block2", "block3"]
        # 경로 2: ["block1", "block3"]
        assert ["block1", "block2", "block3"] in paths
        assert ["block1", "block3"] in paths

    def test_validate_success(self):
        """검증 성공"""
        graph = BlockGraph()

        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        node2 = BlockNode("block2", 2, "Block 2", entry_conditions=["true"])

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(BlockEdge("block1", "block2"))

        errors = graph.validate()
        assert len(errors) == 0

    def test_validate_missing_root(self):
        """루트 노드 없음 - 검증 실패"""
        graph = BlockGraph()
        graph.root_node_id = None

        errors = graph.validate()
        assert any("루트 노드" in err for err in errors)

    def test_complex_graph_with_branching_and_merging(self):
        """복잡한 그래프: 분기 + 병합"""
        graph = BlockGraph()

        # 노드 생성
        node1 = BlockNode("block1", 1, "Block 1", entry_conditions=["true"])
        node2a = BlockNode("block2a", 2, "Block 2A", entry_conditions=["true"])
        node2b = BlockNode("block2b", 2, "Block 2B", entry_conditions=["true"])
        node3 = BlockNode("block3", 3, "Block 3", entry_conditions=["true"])

        graph.add_node(node1)
        graph.add_node(node2a)
        graph.add_node(node2b)
        graph.add_node(node3)

        # 그래프 구조:
        # block1 → block2a → block3
        #       ↘ block2b ↗
        graph.add_edge(BlockEdge("block1", "block2a", priority=1))
        graph.add_edge(BlockEdge("block1", "block2b", priority=2))
        graph.add_edge(BlockEdge("block2a", "block3"))
        graph.add_edge(BlockEdge("block2b", "block3"))

        # 검증
        errors = graph.validate()
        assert len(errors) == 0

        # Block1의 자식은 Block2A, Block2B
        children_b1 = graph.get_children("block1")
        assert len(children_b1) == 2

        # Block3의 부모는 Block2A, Block2B
        parents_b3 = graph.get_parents("block3")
        assert len(parents_b3) == 2

        # 경로 확인: Block1 → Block3 (2개의 경로)
        paths = graph.get_all_paths("block1", "block3")
        assert len(paths) == 2
        assert ["block1", "block2a", "block3"] in paths
        assert ["block1", "block2b", "block3"] in paths
