"""
BlockGraph - 블록 그래프 관리

블록 노드와 엣지로 구성된 DAG(Directed Acyclic Graph)를 관리.
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field

from .block_node import BlockNode
from .block_edge import BlockEdge, EdgeType


@dataclass
class BlockGraph:
    """
    블록 그래프

    블록들 간의 관계를 DAG(Directed Acyclic Graph)로 표현.

    Features:
    - 분기 (Branching): 하나의 블록에서 여러 블록으로 전이
    - 건너뛰기 (Skipping): 중간 블록 스킵 (Block1 → Block3)
    - 조건부 전이 (Conditional): 조건에 따라 다음 블록 선택
    - 다중 부모 (Multi-parent): 여러 블록이 하나의 블록으로 전이

    Attributes:
        nodes: 블록 노드 딕셔너리 (block_id → BlockNode)
        edges: 엣지 리스트
        root_node_id: 시작 블록 ID (일반적으로 "block1")
    """

    nodes: Dict[str, BlockNode] = field(default_factory=dict)
    edges: List[BlockEdge] = field(default_factory=list)
    root_node_id: Optional[str] = None

    def add_node(self, node: BlockNode) -> None:
        """
        노드 추가

        Args:
            node: 추가할 블록 노드

        Raises:
            ValueError: 노드 ID가 중복되는 경우
        """
        if node.block_id in self.nodes:
            raise ValueError(f"이미 존재하는 블록 ID: {node.block_id}")

        self.nodes[node.block_id] = node

        # 첫 번째 노드를 루트로 설정
        if self.root_node_id is None:
            self.root_node_id = node.block_id

    def add_edge(self, edge: BlockEdge) -> None:
        """
        엣지 추가

        Args:
            edge: 추가할 엣지

        Raises:
            ValueError: 노드가 존재하지 않거나 순환이 발생하는 경우
        """
        # 노드 존재 확인
        if edge.from_block_id not in self.nodes:
            raise ValueError(f"알 수 없는 블록 ID: {edge.from_block_id}")

        if edge.to_block_id not in self.nodes:
            raise ValueError(f"알 수 없는 블록 ID: {edge.to_block_id}")

        # 순환 확인 (DAG 유지)
        if self._creates_cycle(edge):
            raise ValueError(
                f"순환이 발생합니다: {edge.from_block_id} → {edge.to_block_id}"
            )

        self.edges.append(edge)

    def get_node(self, block_id: str) -> Optional[BlockNode]:
        """블록 노드 조회"""
        return self.nodes.get(block_id)

    def get_children(self, block_id: str) -> List[BlockNode]:
        """
        자식 블록들 조회

        Args:
            block_id: 부모 블록 ID

        Returns:
            자식 블록 노드 리스트 (우선순위 순으로 정렬)
        """
        child_edges = [
            edge for edge in self.edges
            if edge.from_block_id == block_id
        ]

        # 우선순위로 정렬
        child_edges.sort(key=lambda e: e.priority)

        return [self.nodes[edge.to_block_id] for edge in child_edges]

    def get_parents(self, block_id: str) -> List[BlockNode]:
        """
        부모 블록들 조회

        Args:
            block_id: 자식 블록 ID

        Returns:
            부모 블록 노드 리스트
        """
        parent_edges = [
            edge for edge in self.edges
            if edge.to_block_id == block_id
        ]

        return [self.nodes[edge.from_block_id] for edge in parent_edges]

    def get_edges_from(self, block_id: str) -> List[BlockEdge]:
        """특정 블록에서 나가는 엣지들 조회"""
        return [edge for edge in self.edges if edge.from_block_id == block_id]

    def get_edges_to(self, block_id: str) -> List[BlockEdge]:
        """특정 블록으로 들어오는 엣지들 조회"""
        return [edge for edge in self.edges if edge.to_block_id == block_id]

    def get_all_paths(self, from_block_id: str, to_block_id: str) -> List[List[str]]:
        """
        두 블록 간의 모든 경로 찾기

        Args:
            from_block_id: 시작 블록 ID
            to_block_id: 도착 블록 ID

        Returns:
            경로 리스트 (각 경로는 블록 ID 리스트)
        """
        paths = []
        self._find_all_paths(from_block_id, to_block_id, [from_block_id], paths)
        return paths

    def _find_all_paths(
        self,
        current: str,
        target: str,
        path: List[str],
        paths: List[List[str]]
    ) -> None:
        """DFS로 모든 경로 찾기 (재귀)"""
        if current == target:
            paths.append(path.copy())
            return

        for child in self.get_children(current):
            if child.block_id not in path:  # 순환 방지
                path.append(child.block_id)
                self._find_all_paths(child.block_id, target, path, paths)
                path.pop()

    def topological_sort(self) -> List[str]:
        """
        위상 정렬 (Topological Sort)

        Returns:
            블록 ID 리스트 (의존성 순서대로)

        Raises:
            ValueError: 순환이 존재하는 경우
        """
        # 진입 차수(in-degree) 계산
        in_degree = {node_id: 0 for node_id in self.nodes}
        for edge in self.edges:
            in_degree[edge.to_block_id] += 1

        # 진입 차수가 0인 노드들로 시작
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # 현재 노드에서 나가는 엣지들 처리
            for edge in self.get_edges_from(current):
                in_degree[edge.to_block_id] -= 1
                if in_degree[edge.to_block_id] == 0:
                    queue.append(edge.to_block_id)

        # 모든 노드가 처리되었는지 확인
        if len(result) != len(self.nodes):
            raise ValueError("그래프에 순환이 존재합니다 (DAG가 아님)")

        return result

    def _creates_cycle(self, new_edge: BlockEdge) -> bool:
        """
        새로운 엣지가 순환을 만드는지 확인

        Args:
            new_edge: 추가할 엣지

        Returns:
            순환을 만들면 True, 아니면 False
        """
        # 임시로 엣지 추가
        temp_edges = self.edges + [new_edge]

        # DFS로 순환 확인
        visited = set()
        rec_stack = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            # 모든 자식 노드 확인
            for edge in temp_edges:
                if edge.from_block_id == node_id:
                    child_id = edge.to_block_id

                    if child_id not in visited:
                        if has_cycle(child_id):
                            return True
                    elif child_id in rec_stack:
                        return True  # 순환 발견

            rec_stack.remove(node_id)
            return False

        # 모든 노드에서 순환 확인
        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    return True

        return False

    def validate(self) -> List[str]:
        """
        그래프 전체 유효성 검증

        Returns:
            오류 메시지 리스트 (빈 리스트 = 검증 성공)
        """
        errors = []

        # 루트 노드 확인
        if not self.root_node_id:
            errors.append("루트 노드가 설정되지 않았습니다")
        elif self.root_node_id not in self.nodes:
            errors.append(f"루트 노드를 찾을 수 없습니다: {self.root_node_id}")

        # 모든 노드 검증
        for node_id, node in self.nodes.items():
            node_errors = node.validate()
            for err in node_errors:
                errors.append(f"[{node_id}] {err}")

        # 모든 엣지 검증
        for i, edge in enumerate(self.edges):
            edge_errors = edge.validate()
            for err in edge_errors:
                errors.append(f"[Edge {i}] {err}")

            # 엣지의 노드 존재 확인
            if edge.from_block_id not in self.nodes:
                errors.append(f"[Edge {i}] 알 수 없는 from_block_id: {edge.from_block_id}")

            if edge.to_block_id not in self.nodes:
                errors.append(f"[Edge {i}] 알 수 없는 to_block_id: {edge.to_block_id}")

        # DAG 검증 (순환 없는지)
        try:
            self.topological_sort()
        except ValueError as e:
            errors.append(f"DAG 검증 실패: {e}")

        return errors

    def __repr__(self) -> str:
        return (
            f"BlockGraph(nodes={len(self.nodes)}, edges={len(self.edges)}, "
            f"root='{self.root_node_id}')"
        )
