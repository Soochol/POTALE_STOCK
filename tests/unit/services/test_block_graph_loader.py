"""
BlockGraphLoader 단위 테스트
"""
import pytest
import tempfile
from pathlib import Path

from src.application.services.block_graph_loader import BlockGraphLoader
from src.domain.entities.block_graph import BlockGraph, BlockNode, BlockEdge, EdgeType


class TestBlockGraphLoader:
    """BlockGraphLoader 테스트"""

    def test_load_simple_graph_from_dict(self):
        """단순 그래프 로드"""
        data = {
            'block_graph': {
                'root_node': 'block1',
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Block 1',
                        'entry_conditions': ['current.close >= 10000']
                    },
                    'block2': {
                        'block_id': 'block2',
                        'block_type': 2,
                        'name': 'Block 2',
                        'entry_conditions': ['EXISTS("block1")']
                    }
                },
                'edges': [
                    {
                        'from_block': 'block1',
                        'to_block': 'block2'
                    }
                ]
            }
        }

        loader = BlockGraphLoader()
        graph = loader.load_from_dict(data)

        assert len(graph.nodes) == 2
        assert 'block1' in graph.nodes
        assert 'block2' in graph.nodes
        assert len(graph.edges) == 1
        assert graph.root_node_id == 'block1'

    def test_load_nodes_with_full_structure(self):
        """전체 구조를 가진 노드 로드"""
        data = {
            'block_graph': {
                'root_node': 'block1',
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Initial Surge',
                        'description': 'First block',
                        'entry_conditions': [
                            {
                                'name': 'price_check',
                                'expression': 'current.close >= 10000',
                                'description': 'Price threshold'
                            },
                            'current.volume >= 1000000'
                        ],
                        'exit_conditions': [
                            'current.close < ma(120)'
                        ],
                        'parameters': {
                            'min_duration': 1,
                            'max_duration': 50
                        },
                        'metadata': {
                            'note': 'test'
                        }
                    }
                },
                'edges': []
            }
        }

        loader = BlockGraphLoader()
        graph = loader.load_from_dict(data)

        node = graph.nodes['block1']
        assert node.block_id == 'block1'
        assert node.block_type == 1
        assert node.name == 'Initial Surge'
        assert node.description == 'First block'
        assert len(node.entry_conditions) == 2
        assert 'current.close >= 10000' in node.entry_conditions
        assert 'current.volume >= 1000000' in node.entry_conditions
        assert len(node.exit_conditions) == 1
        assert node.parameters['min_duration'] == 1
        assert node.metadata['note'] == 'test'

    def test_load_edges_with_types(self):
        """다양한 엣지 타입 로드"""
        data = {
            'block_graph': {
                'root_node': 'block1',
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Block 1',
                        'entry_conditions': ['true']
                    },
                    'block2a': {
                        'block_id': 'block2a',
                        'block_type': 2,
                        'name': 'Block 2A',
                        'entry_conditions': ['true']
                    },
                    'block2b': {
                        'block_id': 'block2b',
                        'block_type': 2,
                        'name': 'Block 2B',
                        'entry_conditions': ['true']
                    }
                },
                'edges': [
                    {
                        'from_block': 'block1',
                        'to_block': 'block2a',
                        'edge_type': 'conditional',
                        'condition': 'current.volume >= 1000000',
                        'priority': 1
                    },
                    {
                        'from_block': 'block1',
                        'to_block': 'block2b',
                        'edge_type': 'optional',
                        'priority': 2
                    }
                ]
            }
        }

        loader = BlockGraphLoader()
        graph = loader.load_from_dict(data)

        assert len(graph.edges) == 2

        # 첫 번째 엣지 (conditional)
        edge1 = graph.edges[0]
        assert edge1.from_block_id == 'block1'
        assert edge1.to_block_id == 'block2a'
        assert edge1.edge_type == EdgeType.CONDITIONAL
        assert edge1.condition == 'current.volume >= 1000000'
        assert edge1.priority == 1

        # 두 번째 엣지 (optional)
        edge2 = graph.edges[1]
        assert edge2.from_block_id == 'block1'
        assert edge2.to_block_id == 'block2b'
        assert edge2.edge_type == EdgeType.OPTIONAL
        assert edge2.priority == 2

    def test_load_missing_block_graph_key(self):
        """block_graph 키 없음 - 실패"""
        data = {
            'wrong_key': {}
        }

        loader = BlockGraphLoader()

        with pytest.raises(ValueError, match="'block_graph'"):
            loader.load_from_dict(data)

    def test_load_missing_block_type(self):
        """block_type 없음 - 실패"""
        data = {
            'block_graph': {
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        # block_type 없음!
                        'name': 'Block 1',
                        'entry_conditions': ['true']
                    }
                }
            }
        }

        loader = BlockGraphLoader()

        with pytest.raises(ValueError, match="block_type"):
            loader.load_from_dict(data)

    def test_load_missing_name(self):
        """name 없음 - 실패"""
        data = {
            'block_graph': {
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        # name 없음!
                        'entry_conditions': ['true']
                    }
                }
            }
        }

        loader = BlockGraphLoader()

        with pytest.raises(ValueError, match="name"):
            loader.load_from_dict(data)

    def test_load_invalid_edge_type(self):
        """잘못된 edge_type - 실패"""
        data = {
            'block_graph': {
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Block 1',
                        'entry_conditions': ['true']
                    },
                    'block2': {
                        'block_id': 'block2',
                        'block_type': 2,
                        'name': 'Block 2',
                        'entry_conditions': ['true']
                    }
                },
                'edges': [
                    {
                        'from_block': 'block1',
                        'to_block': 'block2',
                        'edge_type': 'invalid_type'
                    }
                ]
            }
        }

        loader = BlockGraphLoader()

        with pytest.raises(ValueError, match="알 수 없는 edge_type"):
            loader.load_from_dict(data)

    def test_load_creates_cycle_fails(self):
        """순환 생성 시 검증 실패"""
        data = {
            'block_graph': {
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Block 1',
                        'entry_conditions': ['true']
                    },
                    'block2': {
                        'block_id': 'block2',
                        'block_type': 2,
                        'name': 'Block 2',
                        'entry_conditions': ['true']
                    }
                },
                'edges': [
                    {
                        'from_block': 'block1',
                        'to_block': 'block2'
                    },
                    {
                        'from_block': 'block2',
                        'to_block': 'block1'  # 순환!
                    }
                ]
            }
        }

        loader = BlockGraphLoader()

        with pytest.raises(ValueError, match="순환"):
            loader.load_from_dict(data)

    def test_save_and_load_roundtrip(self):
        """저장 후 로드 (왕복)"""
        # 원본 그래프 생성
        original_graph = BlockGraph()

        node1 = BlockNode(
            block_id='block1',
            block_type=1,
            name='Block 1',
            description='Test block',
            entry_conditions=['current.close >= 10000'],
            exit_conditions=['current.close < ma(120)'],
            parameters={'min_duration': 1}
        )

        node2 = BlockNode(
            block_id='block2',
            block_type=2,
            name='Block 2',
            entry_conditions=['EXISTS("block1")']
        )

        original_graph.add_node(node1)
        original_graph.add_node(node2)
        original_graph.add_edge(BlockEdge('block1', 'block2'))

        # 딕셔너리로 변환
        loader = BlockGraphLoader()
        data = loader.save_to_dict(original_graph)

        # 딕셔너리에서 다시 로드
        loaded_graph = loader.load_from_dict(data)

        # 비교
        assert len(loaded_graph.nodes) == len(original_graph.nodes)
        assert len(loaded_graph.edges) == len(original_graph.edges)
        assert loaded_graph.root_node_id == original_graph.root_node_id

        # 노드 비교
        loaded_node1 = loaded_graph.nodes['block1']
        assert loaded_node1.block_id == node1.block_id
        assert loaded_node1.block_type == node1.block_type
        assert loaded_node1.name == node1.name
        assert loaded_node1.entry_conditions == node1.entry_conditions
        assert loaded_node1.parameters == node1.parameters

    def test_load_from_file_not_found(self):
        """파일 없음 - FileNotFoundError"""
        loader = BlockGraphLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_from_file("nonexistent_file.yaml")

    def test_load_and_save_file(self):
        """파일 로드 및 저장"""
        data = {
            'block_graph': {
                'root_node': 'block1',
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Block 1',
                        'entry_conditions': ['current.close >= 10000']
                    }
                },
                'edges': []
            }
        }

        loader = BlockGraphLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "test_graph.yaml"

            # 딕셔너리에서 그래프 로드
            graph = loader.load_from_dict(data)

            # 파일로 저장
            loader.save_to_file(graph, str(yaml_path))

            # 파일이 생성되었는지 확인
            assert yaml_path.exists()

            # 파일에서 다시 로드
            loaded_graph = loader.load_from_file(str(yaml_path))

            # 비교
            assert len(loaded_graph.nodes) == 1
            assert 'block1' in loaded_graph.nodes

    def test_block_id_defaults_to_key(self):
        """block_id가 없으면 키를 사용"""
        data = {
            'block_graph': {
                'nodes': {
                    'my_block': {
                        # block_id 없음 - 키 'my_block'을 사용
                        'block_type': 1,
                        'name': 'My Block',
                        'entry_conditions': ['true']
                    }
                }
            }
        }

        loader = BlockGraphLoader()
        graph = loader.load_from_dict(data)

        node = graph.nodes['my_block']
        assert node.block_id == 'my_block'

    def test_edge_default_type_is_sequential(self):
        """edge_type 기본값은 sequential"""
        data = {
            'block_graph': {
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Block 1',
                        'entry_conditions': ['true']
                    },
                    'block2': {
                        'block_id': 'block2',
                        'block_type': 2,
                        'name': 'Block 2',
                        'entry_conditions': ['true']
                    }
                },
                'edges': [
                    {
                        'from_block': 'block1',
                        'to_block': 'block2'
                        # edge_type 없음 - sequential이 기본값
                    }
                ]
            }
        }

        loader = BlockGraphLoader()
        graph = loader.load_from_dict(data)

        edge = graph.edges[0]
        assert edge.edge_type == EdgeType.SEQUENTIAL

    def test_load_seed_pattern_type(self):
        """pattern_type이 "seed"인 경우"""
        data = {
            'block_graph': {
                'pattern_type': 'seed',
                'root_node': 'block1',
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Seed Block1',
                        'entry_conditions': ['true']
                    }
                }
            }
        }

        loader = BlockGraphLoader()
        graph = loader.load_from_dict(data)

        assert graph.pattern_type == 'seed'
        assert graph.redetection_config is None

    def test_load_redetection_pattern_type_with_config(self):
        """pattern_type이 "redetection"이고 redetection_config가 있는 경우"""
        data = {
            'block_graph': {
                'pattern_type': 'redetection',
                'root_node': 'block1',
                'redetection_config': {
                    'seed_pattern_reference': 'seed_v1',
                    'tolerance': {
                        'price_range': 0.08,
                        'volume_range': 0.35,
                        'time_range': 12
                    },
                    'matching_weights': {
                        'price_shape': 0.5,
                        'volume_shape': 0.3,
                        'timing': 0.2
                    },
                    'min_similarity_score': 0.75,
                    'min_detection_interval_days': 25
                },
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Redetection Block1',
                        'entry_conditions': ['true']
                    }
                }
            }
        }

        loader = BlockGraphLoader()
        graph = loader.load_from_dict(data)

        assert graph.pattern_type == 'redetection'
        assert graph.redetection_config is not None
        assert graph.redetection_config.seed_pattern_reference == 'seed_v1'
        assert graph.redetection_config.tolerance.price_range == 0.08
        assert graph.redetection_config.matching_weights.price_shape == 0.5
        assert graph.redetection_config.min_similarity_score == 0.75

    def test_load_redetection_without_config(self):
        """pattern_type이 "redetection"이지만 redetection_config가 없는 경우"""
        data = {
            'block_graph': {
                'pattern_type': 'redetection',
                'root_node': 'block1',
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Redetection Block1',
                        'entry_conditions': ['true']
                    }
                }
            }
        }

        loader = BlockGraphLoader()
        graph = loader.load_from_dict(data)

        # pattern_type은 redetection이지만 config는 None
        assert graph.pattern_type == 'redetection'
        assert graph.redetection_config is None

    def test_invalid_pattern_type(self):
        """잘못된 pattern_type"""
        data = {
            'block_graph': {
                'pattern_type': 'invalid_type',
                'root_node': 'block1',
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Block1',
                        'entry_conditions': ['true']
                    }
                }
            }
        }

        loader = BlockGraphLoader()

        with pytest.raises(ValueError, match="Invalid pattern_type"):
            loader.load_from_dict(data)

    def test_save_seed_pattern_to_dict(self):
        """Seed pattern을 딕셔너리로 저장"""
        from src.domain.entities.block_graph import BlockGraph, BlockNode

        graph = BlockGraph()
        graph.pattern_type = 'seed'
        graph.root_node_id = 'block1'

        node = BlockNode(
            block_id='block1',
            block_type=1,
            name='Seed Block1',
            entry_conditions=['true'],
            exit_conditions=[]
        )
        graph.add_node(node)

        loader = BlockGraphLoader()
        data = loader.save_to_dict(graph)

        assert data['block_graph']['pattern_type'] == 'seed'
        assert 'redetection_config' not in data['block_graph']

    def test_save_redetection_pattern_to_dict(self):
        """Redetection pattern을 딕셔너리로 저장"""
        from src.domain.entities.block_graph import BlockGraph, BlockNode
        from src.domain.entities.patterns import RedetectionConfig, ToleranceConfig

        graph = BlockGraph()
        graph.pattern_type = 'redetection'
        graph.root_node_id = 'block1'
        graph.redetection_config = RedetectionConfig(
            seed_pattern_reference='seed_v1',
            tolerance=ToleranceConfig(price_range=0.10),
            min_similarity_score=0.80
        )

        node = BlockNode(
            block_id='block1',
            block_type=1,
            name='Redetection Block1',
            entry_conditions=['true'],
            exit_conditions=[]
        )
        graph.add_node(node)

        loader = BlockGraphLoader()
        data = loader.save_to_dict(graph)

        assert data['block_graph']['pattern_type'] == 'redetection'
        assert 'redetection_config' in data['block_graph']
        assert data['block_graph']['redetection_config']['seed_pattern_reference'] == 'seed_v1'
        assert data['block_graph']['redetection_config']['tolerance']['price_range'] == 0.10
        assert data['block_graph']['redetection_config']['min_similarity_score'] == 0.80

    def test_roundtrip_redetection_pattern(self):
        """Redetection pattern roundtrip: save_to_dict → load_from_dict"""
        from src.domain.entities.block_graph import BlockGraph, BlockNode
        from src.domain.entities.patterns import RedetectionConfig

        # Original graph
        original_graph = BlockGraph()
        original_graph.pattern_type = 'redetection'
        original_graph.root_node_id = 'block1'
        original_graph.redetection_config = RedetectionConfig(
            seed_pattern_reference='seed_test',
            min_similarity_score=0.75,
            min_detection_interval_days=15
        )

        node = BlockNode(
            block_id='block1',
            block_type=1,
            name='Test Block',
            entry_conditions=['current.close >= 10000'],
            exit_conditions=['current.close < 9000']
        )
        original_graph.add_node(node)

        # Save to dict
        loader = BlockGraphLoader()
        data = loader.save_to_dict(original_graph)

        # Load from dict
        restored_graph = loader.load_from_dict(data)

        # Compare
        assert restored_graph.pattern_type == original_graph.pattern_type
        assert restored_graph.root_node_id == original_graph.root_node_id
        assert restored_graph.redetection_config is not None
        assert restored_graph.redetection_config.seed_pattern_reference == 'seed_test'
        assert restored_graph.redetection_config.min_similarity_score == 0.75
        assert restored_graph.redetection_config.min_detection_interval_days == 15
