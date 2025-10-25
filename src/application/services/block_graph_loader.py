"""
BlockGraphLoader - YAML에서 BlockGraph 로드

YAML 파일로부터 블록 정의를 읽어 BlockGraph 객체로 변환.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List

from src.domain.entities.block_graph import BlockGraph, BlockNode, BlockEdge, EdgeType
from src.domain.entities.patterns import RedetectionConfig
from src.domain.exceptions import YAMLConfigError, ValidationError
from src.domain.error_context import create_file_operation_context
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class BlockGraphLoader:
    """
    YAML 파일에서 BlockGraph를 로드하는 서비스

    YAML 구조:
        block_graph:
          root_node: "block1"
          nodes:
            block1:
              block_id: "block1"
              block_type: 1
              name: "Initial Surge"
              entry_conditions: [...]
              exit_conditions: [...]
              parameters: {...}
          edges:
            - from_block: "block1"
              to_block: "block2"
              edge_type: "sequential"
    """

    def load_from_file(self, yaml_path: str) -> BlockGraph:
        """
        YAML 파일에서 BlockGraph 로드

        Args:
            yaml_path: YAML 파일 경로

        Returns:
            BlockGraph 객체

        Raises:
            YAMLConfigError: YAML 파일 읽기/파싱 실패
            ValidationError: YAML 구조가 잘못된 경우
        """
        path = Path(yaml_path)
        context = create_file_operation_context(
            file_path=str(path),
            operation='parse'
        )

        # 파일 존재 확인
        if not path.exists():
            logger.error("YAML file not found", context=context)
            raise YAMLConfigError(
                f"YAML 파일을 찾을 수 없습니다: {yaml_path}",
                context=context
            )

        # YAML 파일 읽기
        try:
            logger.debug("Loading YAML file", context=context)
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error("YAML parsing failed", context=context, exc=e)
            raise YAMLConfigError(
                f"YAML 파싱 실패: {yaml_path}",
                context={**context, 'yaml_error': str(e)}
            ) from e
        except IOError as e:
            logger.error("File read failed", context=context, exc=e)
            raise YAMLConfigError(
                f"파일 읽기 실패: {yaml_path}",
                context={**context, 'io_error': str(e)}
            ) from e
        except Exception as e:
            logger.error("Unexpected error during YAML loading", context=context, exc=e)
            raise YAMLConfigError(
                f"YAML 로드 중 예상치 못한 오류: {yaml_path}",
                context=context
            ) from e

        # 딕셔너리로 변환
        try:
            return self.load_from_dict(data)
        except Exception as e:
            logger.error("BlockGraph construction failed", context=context, exc=e)
            raise

    def load_from_dict(self, data: Dict[str, Any]) -> BlockGraph:
        """
        딕셔너리에서 BlockGraph 로드

        Args:
            data: YAML에서 로드한 딕셔너리

        Returns:
            BlockGraph 객체

        Raises:
            ValidationError: 데이터 구조가 잘못된 경우
        """
        logger.debug("Loading BlockGraph from dictionary")

        # 'block_graph' 키 확인
        if 'block_graph' not in data:
            error_msg = "YAML 파일에 'block_graph' 키가 없습니다"
            logger.error(error_msg)
            raise ValidationError(error_msg)

        graph_data = data['block_graph']

        # BlockGraph 생성
        graph = BlockGraph()

        # 패턴 타입 설정 (기본값: "seed")
        pattern_type = graph_data.get('pattern_type', 'seed')
        if pattern_type not in ['seed', 'redetection']:
            error_msg = f"Invalid pattern_type: {pattern_type}. Must be 'seed' or 'redetection'"
            logger.error(error_msg, context={'pattern_type': pattern_type})
            raise ValidationError(error_msg, context={'pattern_type': pattern_type})
        graph.pattern_type = pattern_type
        logger.debug(f"Pattern type set to: {pattern_type}")

        # 재탐지 설정 로드 (pattern_type이 "redetection"인 경우)
        if pattern_type == 'redetection' and 'redetection_config' in graph_data:
            graph.redetection_config = RedetectionConfig.from_dict(graph_data['redetection_config'])
            logger.debug("Redetection config loaded")

        # 루트 노드 설정
        root_node_id = graph_data.get('root_node')
        if root_node_id:
            graph.root_node_id = root_node_id
            logger.debug(f"Root node set to: {root_node_id}")

        # 노드 로드
        if 'nodes' in graph_data:
            nodes = self._load_nodes(graph_data['nodes'])
            for node in nodes:
                graph.add_node(node)
            logger.debug(f"Loaded {len(nodes)} nodes")

        # 엣지 로드
        if 'edges' in graph_data:
            edges = self._load_edges(graph_data['edges'])
            for edge in edges:
                graph.add_edge(edge)
            logger.debug(f"Loaded {len(edges)} edges")

        # 검증
        errors = graph.validate()
        if errors:
            error_msg = f"BlockGraph 검증 실패:\n" + "\n".join(errors)
            logger.error("BlockGraph validation failed", context={'errors': errors})
            raise ValidationError(
                error_msg,
                context={'validation_errors': errors}
            )

        logger.info("BlockGraph loaded successfully", context={
            'pattern_type': pattern_type,
            'num_nodes': len(graph.nodes),
            'num_edges': len(graph.edges)
        })

        return graph

    def _load_nodes(self, nodes_data: Dict[str, Any]) -> List[BlockNode]:
        """
        노드 데이터에서 BlockNode 리스트 생성

        Args:
            nodes_data: 노드 데이터 딕셔너리
                예: {
                    "block1": {
                        "block_id": "block1",
                        "block_type": 1,
                        "name": "Initial Surge",
                        ...
                    }
                }

        Returns:
            BlockNode 리스트
        """
        nodes = []

        for node_id, node_data in nodes_data.items():
            # 필수 필드 확인
            if 'block_id' not in node_data:
                node_data['block_id'] = node_id  # block_id가 없으면 키 사용

            if 'block_type' not in node_data:
                error_msg = f"노드 '{node_id}'에 block_type이 없습니다"
                logger.error(error_msg, context={'node_id': node_id})
                raise ValidationError(error_msg, context={'node_id': node_id})

            if 'name' not in node_data:
                error_msg = f"노드 '{node_id}'에 name이 없습니다"
                logger.error(error_msg, context={'node_id': node_id})
                raise ValidationError(error_msg, context={'node_id': node_id})

            # 조건 변환: 리스트[객체] → 리스트[문자열]
            entry_conditions = self._extract_condition_expressions(
                node_data.get('entry_conditions', [])
            )
            exit_conditions = self._extract_condition_expressions(
                node_data.get('exit_conditions', [])
            )

            # spot_condition 추출 (문자열 또는 None)
            spot_condition = node_data.get('spot_condition')

            # BlockNode 생성
            node = BlockNode(
                block_id=node_data['block_id'],
                block_type=node_data['block_type'],
                name=node_data['name'],
                description=node_data.get('description', ''),
                entry_conditions=entry_conditions,
                exit_conditions=exit_conditions,
                spot_condition=spot_condition,
                parameters=node_data.get('parameters', {}),
                metadata=node_data.get('metadata', {})
            )

            nodes.append(node)

        return nodes

    def _extract_condition_expressions(self, conditions: List) -> List[str]:
        """
        조건 데이터에서 표현식 추출

        조건은 두 가지 형식 지원:
        1. 문자열: "current.close >= 10000"
        2. 객체: {"name": "price_check", "expression": "current.close >= 10000"}

        Args:
            conditions: 조건 리스트

        Returns:
            표현식 문자열 리스트
        """
        expressions = []

        for cond in conditions:
            if isinstance(cond, str):
                # 문자열 형식
                expressions.append(cond)
            elif isinstance(cond, dict):
                # 객체 형식
                if 'expression' not in cond:
                    error_msg = f"조건 객체에 'expression' 키가 없습니다: {cond}"
                    logger.error(error_msg, context={'condition': cond})
                    raise ValidationError(error_msg, context={'condition': cond})
                expressions.append(cond['expression'])
            else:
                error_msg = f"잘못된 조건 형식: {cond}"
                logger.error(error_msg, context={'condition': cond, 'type': type(cond).__name__})
                raise ValidationError(error_msg, context={'condition': cond})

        return expressions

    def _load_edges(self, edges_data: List[Dict[str, Any]]) -> List[BlockEdge]:
        """
        엣지 데이터에서 BlockEdge 리스트 생성

        Args:
            edges_data: 엣지 데이터 리스트
                예: [
                    {
                        "from_block": "block1",
                        "to_block": "block2",
                        "edge_type": "sequential",
                        "priority": 1
                    }
                ]

        Returns:
            BlockEdge 리스트
        """
        edges = []

        for edge_data in edges_data:
            # 필수 필드 확인
            if 'from_block' not in edge_data:
                error_msg = f"엣지에 'from_block'이 없습니다: {edge_data}"
                logger.error(error_msg, context={'edge_data': edge_data})
                raise ValidationError(error_msg, context={'edge_data': edge_data})

            if 'to_block' not in edge_data:
                error_msg = f"엣지에 'to_block'이 없습니다: {edge_data}"
                logger.error(error_msg, context={'edge_data': edge_data})
                raise ValidationError(error_msg, context={'edge_data': edge_data})

            # EdgeType 변환
            edge_type_str = edge_data.get('edge_type', 'sequential')
            try:
                edge_type = EdgeType(edge_type_str)
            except ValueError as e:
                error_msg = (
                    f"알 수 없는 edge_type: {edge_type_str}. "
                    f"가능한 값: sequential, conditional, optional, branching"
                )
                logger.error(error_msg, context={'edge_type': edge_type_str, 'edge_data': edge_data})
                raise ValidationError(
                    error_msg,
                    context={'edge_type': edge_type_str, 'edge_data': edge_data}
                ) from e

            # BlockEdge 생성
            edge = BlockEdge(
                from_block_id=edge_data['from_block'],
                to_block_id=edge_data['to_block'],
                edge_type=edge_type,
                condition=edge_data.get('condition'),
                priority=edge_data.get('priority', 0),
                metadata=edge_data.get('metadata', {})
            )

            edges.append(edge)

        return edges

    def save_to_file(self, graph: BlockGraph, yaml_path: str) -> None:
        """
        BlockGraph를 YAML 파일로 저장

        Args:
            graph: BlockGraph 객체
            yaml_path: 저장할 YAML 파일 경로
        """
        data = self.save_to_dict(graph)

        path = Path(yaml_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, indent=2)

    def save_to_dict(self, graph: BlockGraph) -> Dict[str, Any]:
        """
        BlockGraph를 딕셔너리로 변환

        Args:
            graph: BlockGraph 객체

        Returns:
            YAML 저장용 딕셔너리
        """
        nodes_data = {}

        for node_id, node in graph.nodes.items():
            nodes_data[node_id] = {
                'block_id': node.block_id,
                'block_type': node.block_type,
                'name': node.name,
                'description': node.description,
                'entry_conditions': [
                    {'expression': expr} for expr in node.entry_conditions
                ],
                'exit_conditions': [
                    {'expression': expr} for expr in node.exit_conditions
                ],
                'parameters': node.parameters,
                'metadata': node.metadata
            }

        edges_data = []
        for edge in graph.edges:
            edge_dict = {
                'from_block': edge.from_block_id,
                'to_block': edge.to_block_id,
                'edge_type': edge.edge_type.value,
                'priority': edge.priority
            }

            if edge.condition:
                edge_dict['condition'] = edge.condition

            if edge.metadata:
                edge_dict['metadata'] = edge.metadata

            edges_data.append(edge_dict)

        result = {
            'block_graph': {
                'pattern_type': graph.pattern_type,
                'root_node': graph.root_node_id,
                'nodes': nodes_data,
                'edges': edges_data
            }
        }

        # Redetection 설정 추가 (pattern_type이 "redetection"이고 설정이 있는 경우)
        if graph.pattern_type == 'redetection' and graph.redetection_config:
            result['block_graph']['redetection_config'] = graph.redetection_config.to_dict()

        return result
