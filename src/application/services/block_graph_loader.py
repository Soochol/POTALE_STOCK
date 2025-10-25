"""
BlockGraphLoader - YAML에서 BlockGraph 로드

YAML 파일로부터 블록 정의를 읽어 BlockGraph 객체로 변환.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.domain.entities.block_graph import BlockGraph, BlockNode, BlockEdge, EdgeType
from src.domain.entities.conditions import Condition
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

            # 조건 변환: 리스트[dict/str] → 리스트[Condition]
            entry_conditions = self._parse_conditions(
                node_data.get('entry_conditions', [])
            )
            exit_conditions = self._parse_conditions(
                node_data.get('exit_conditions', [])
            )

            # spot_condition 추출 (Condition 객체 또는 None)
            spot_condition = self._parse_single_condition(
                node_data.get('spot_condition')
            )

            # spot_entry_conditions 추출 (NEW - 2025-10-25)
            spot_entry_conditions = None
            if 'spot_entry_conditions' in node_data:
                spot_entry_conditions = self._parse_conditions(
                    node_data['spot_entry_conditions']
                )

            # 재탐지 조건 추출 (NEW - 2025-10-25)
            redetection_entry_conditions = None
            redetection_exit_conditions = None

            if 'redetection' in node_data:
                redetection_data = node_data['redetection']
                if 'entry_conditions' in redetection_data:
                    redetection_entry_conditions = self._parse_conditions(
                        redetection_data['entry_conditions']
                    )
                if 'exit_conditions' in redetection_data:
                    redetection_exit_conditions = self._parse_conditions(
                        redetection_data['exit_conditions']
                    )

            # BlockNode 생성
            node = BlockNode(
                block_id=node_data['block_id'],
                block_type=node_data['block_type'],
                name=node_data['name'],
                description=node_data.get('description', ''),
                entry_conditions=entry_conditions,
                exit_conditions=exit_conditions,
                spot_condition=spot_condition,
                spot_entry_conditions=spot_entry_conditions,
                redetection_entry_conditions=redetection_entry_conditions,
                redetection_exit_conditions=redetection_exit_conditions,
                parameters=node_data.get('parameters', {}),
                metadata=node_data.get('metadata', {})
            )

            nodes.append(node)

        return nodes

    def _parse_conditions(self, conditions: List) -> List[Condition]:
        """
        조건 데이터를 Condition 객체 리스트로 변환

        조건은 두 가지 형식 지원 (하위 호환):
        1. 문자열: "current.close >= 10000"
        2. 객체: {"name": "price_check", "expression": "current.close >= 10000", "description": "..."}

        Args:
            conditions: 조건 리스트

        Returns:
            Condition 객체 리스트
        """
        condition_objects = []

        for i, cond in enumerate(conditions):
            if isinstance(cond, str):
                # 하위 호환: 문자열 형식
                condition = Condition(
                    name=f"condition_{i}",
                    expression=cond,
                    description=""
                )
            elif isinstance(cond, dict):
                # 표준 형식: dict
                if 'expression' not in cond:
                    error_msg = f"조건 객체에 'expression' 키가 없습니다: {cond}"
                    logger.error(error_msg, context={'condition': cond})
                    raise ValidationError(error_msg, context={'condition': cond})

                condition = Condition(
                    name=cond.get('name', f"condition_{i}"),
                    expression=cond['expression'],
                    description=cond.get('description', '')
                )
            else:
                error_msg = f"잘못된 조건 형식: {cond}"
                logger.error(error_msg, context={'condition': cond, 'type': type(cond).__name__})
                raise ValidationError(error_msg, context={'condition': cond})

            condition_objects.append(condition)

        return condition_objects

    def _parse_single_condition(self, condition_data: Any) -> Optional[Condition]:
        """
        단일 조건 데이터를 Condition 객체로 변환

        Args:
            condition_data: 조건 데이터 (str, dict, 또는 None)

        Returns:
            Condition 객체 또는 None
        """
        if condition_data is None:
            return None

        if isinstance(condition_data, str):
            # 하위 호환: 문자열 형식
            return Condition(
                name="spot_condition",
                expression=condition_data,
                description=""
            )
        elif isinstance(condition_data, dict):
            # 표준 형식: dict
            if 'expression' not in condition_data:
                error_msg = f"조건 객체에 'expression' 키가 없습니다: {condition_data}"
                logger.error(error_msg, context={'condition': condition_data})
                raise ValidationError(error_msg, context={'condition': condition_data})

            return Condition(
                name=condition_data.get('name', 'spot_condition'),
                expression=condition_data['expression'],
                description=condition_data.get('description', '')
            )
        else:
            error_msg = f"잘못된 조건 형식: {condition_data}"
            logger.error(error_msg, context={'condition': condition_data, 'type': type(condition_data).__name__})
            raise ValidationError(error_msg, context={'condition': condition_data})


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
            node_dict = {
                'block_id': node.block_id,
                'block_type': node.block_type,
                'name': node.name,
                'description': node.description,
                'entry_conditions': [
                    {
                        'name': cond.name,
                        'expression': cond.expression,
                        'description': cond.description
                    } for cond in node.entry_conditions
                ],
                'exit_conditions': [
                    {
                        'name': cond.name,
                        'expression': cond.expression,
                        'description': cond.description
                    } for cond in node.exit_conditions
                ],
                'parameters': node.parameters,
                'metadata': node.metadata
            }

            # spot_condition 추가 (있는 경우)
            if node.spot_condition:
                node_dict['spot_condition'] = {
                    'name': node.spot_condition.name,
                    'expression': node.spot_condition.expression,
                    'description': node.spot_condition.description
                }

            nodes_data[node_id] = node_dict

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
