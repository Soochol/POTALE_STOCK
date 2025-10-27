"""
BlockGraphLoader Highlight Condition Tests

BlockGraphLoader의 highlight_condition 파싱 테스트
"""
import pytest
import tempfile
import os

from src.application.services.block_graph_loader import BlockGraphLoader
from src.domain.exceptions import ValidationError


class TestBlockGraphLoaderHighlightCondition:
    """BlockGraphLoader highlight_condition 파싱 테스트"""

    @pytest.fixture
    def loader(self):
        """BlockGraphLoader 인스턴스"""
        return BlockGraphLoader()

    def test_parse_highlight_condition_forward_spot(self, loader):
        """forward_spot 타입 하이라이트 조건 파싱"""
        yaml_content = """
version: "1.0"

block_graph:
  pattern_type: "seed"
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Initial Block"

      entry_conditions:
        - expression: "current.close >= 10000"

      exit_conditions:
        - expression: "exists('block2')"

      # Highlight condition
      highlight_condition:
        type: "forward_spot"
        enabled: true
        priority: 1
        parameters:
          required_spot_count: 2
          consecutive: true
          day_offsets: [1, 2]
        description: "Primary highlight: 2 consecutive volume spots"

  edges: []
"""
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # YAML 로드
            graph = loader.load_from_file(temp_path)

            # BlockNode 검증
            assert len(graph.nodes) == 1
            block1_node = graph.nodes['block1']

            # highlight_condition 검증
            assert block1_node.highlight_condition is not None
            assert block1_node.highlight_condition.type == "forward_spot"
            assert block1_node.highlight_condition.is_enabled() is True
            assert block1_node.highlight_condition.priority == 1
            assert block1_node.highlight_condition.get_parameter("required_spot_count") == 2
            assert block1_node.highlight_condition.get_parameter("consecutive") is True
            assert block1_node.highlight_condition.get_parameter("day_offsets") == [1, 2]
            assert "Primary highlight" in block1_node.highlight_condition.description

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_parse_highlight_condition_disabled(self, loader):
        """비활성화된 하이라이트 조건 파싱"""
        yaml_content = """
version: "1.0"

block_graph:
  pattern_type: "seed"
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Initial Block"

      entry_conditions:
        - expression: "current.close >= 10000"

      exit_conditions:
        - expression: "exists('block2')"

      # Highlight condition (disabled)
      highlight_condition:
        type: "forward_spot"
        enabled: false
        parameters:
          required_spot_count: 2

  edges: []
"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            graph = loader.load_from_file(temp_path)
            block1_node = graph.nodes['block1']

            # 비활성화 확인
            assert block1_node.highlight_condition is not None
            assert block1_node.highlight_condition.is_enabled() is False
            assert block1_node.has_highlight_condition() is False  # enabled=False이므로

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_parse_highlight_condition_missing(self, loader):
        """highlight_condition이 없는 경우 (None)"""
        yaml_content = """
version: "1.0"

block_graph:
  pattern_type: "seed"
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Initial Block"

      entry_conditions:
        - expression: "current.close >= 10000"

      exit_conditions:
        - expression: "exists('block2')"

      # No highlight_condition field

  edges: []
"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            graph = loader.load_from_file(temp_path)
            block1_node = graph.nodes['block1']

            # highlight_condition이 None이어야 함
            assert block1_node.highlight_condition is None
            assert block1_node.has_highlight_condition() is False

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_parse_highlight_condition_missing_type(self, loader):
        """필수 필드 'type'이 없는 경우 ValidationError"""
        yaml_content = """
version: "1.0"

block_graph:
  pattern_type: "seed"
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Initial Block"

      entry_conditions:
        - expression: "current.close >= 10000"

      exit_conditions:
        - expression: "exists('block2')"

      # Missing 'type' field
      highlight_condition:
        enabled: true
        parameters:
          required_spot_count: 2

  edges: []
"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # ValidationError 발생 예상
            with pytest.raises(ValidationError) as exc_info:
                loader.load_from_file(temp_path)

            assert "'type'" in str(exc_info.value)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_parse_highlight_condition_invalid_type(self, loader):
        """잘못된 타입 (문자열 대신 숫자 등)"""
        yaml_content = """
version: "1.0"

block_graph:
  pattern_type: "seed"
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Initial Block"

      entry_conditions:
        - expression: "current.close >= 10000"

      exit_conditions:
        - expression: "exists('block2')"

      # Invalid format (string instead of dict)
      highlight_condition: "invalid_format"

  edges: []
"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # ValidationError 발생 예상
            with pytest.raises(ValidationError) as exc_info:
                loader.load_from_file(temp_path)

            assert "dict 형식" in str(exc_info.value)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_parse_highlight_condition_default_values(self, loader):
        """기본값 테스트 (enabled=True, priority=1)"""
        yaml_content = """
version: "1.0"

block_graph:
  pattern_type: "seed"
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Initial Block"

      entry_conditions:
        - expression: "current.close >= 10000"

      exit_conditions:
        - expression: "exists('block2')"

      # Only 'type' specified (use defaults)
      highlight_condition:
        type: "backward_spot"

  edges: []
"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            graph = loader.load_from_file(temp_path)
            block1_node = graph.nodes['block1']

            # 기본값 확인
            assert block1_node.highlight_condition.type == "backward_spot"
            assert block1_node.highlight_condition.is_enabled() is True  # 기본값
            assert block1_node.highlight_condition.priority == 1  # 기본값
            assert block1_node.highlight_condition.parameters == {}  # 기본값

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_parse_highlight_condition_secondary_priority(self, loader):
        """Secondary 하이라이트 (priority=2)"""
        yaml_content = """
version: "1.0"

block_graph:
  pattern_type: "seed"
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Initial Block"

      entry_conditions:
        - expression: "current.close >= 10000"

      exit_conditions:
        - expression: "exists('block2')"

      highlight_condition:
        type: "forward_spot"
        enabled: true
        priority: 2  # Secondary
        parameters:
          required_spot_count: 2

  edges: []
"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            graph = loader.load_from_file(temp_path)
            block1_node = graph.nodes['block1']

            # Secondary 확인
            assert block1_node.highlight_condition.priority == 2
            assert block1_node.highlight_condition.is_primary() is False

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
