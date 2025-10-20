"""
YAML Condition Repository - YAML 파일을 사용한 조건 저장소 구현
"""
from src.domain.entities import Condition, Rule, RuleType
from typing import List, Optional
from pathlib import Path
import yaml
from rich.console import Console

from ....domain.repositories.condition_repository import IConditionRepository

console = Console()

class YamlConditionRepository(IConditionRepository):
    """YAML 파일을 사용한 조건 저장소"""

    def __init__(self, config_path: str = "config/conditions.yaml"):
        self.config_path = Path(config_path)
        self.console = Console()
        self._ensure_config_exists()

    def _ensure_config_exists(self) -> None:
        """설정 파일이 존재하는지 확인하고 없으면 생성"""
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_to_file({'conditions': []})

    def _load_from_file(self) -> dict:
        """파일에서 데이터 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data if data else {'conditions': []}
        except Exception as e:
            console.print(f"[red]✗[/red] 파일 로드 실패: {str(e)}")
            return {'conditions': []}

    def _save_to_file(self, data: dict) -> bool:
        """파일에 데이터 저장"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            console.print(f"[red]✗[/red] 파일 저장 실패: {str(e)}")
            return False

    def _dict_to_condition(self, data: dict) -> Condition:
        """딕셔너리를 Condition 객체로 변환"""
        rules = []
        for rule_data in data.get('rules', []):
            rule_type = RuleType(rule_data['type'])
            parameters = {k: v for k, v in rule_data.items() if k != 'type'}
            rules.append(Rule(type=rule_type, parameters=parameters))

        return Condition(
            name=data['name'],
            description=data['description'],
            rules=rules
        )

    def _condition_to_dict(self, condition: Condition) -> dict:
        """Condition 객체를 딕셔너리로 변환"""
        rules = []
        for rule in condition.rules:
            rule_dict = {'type': rule.type.value}
            rule_dict.update(rule.parameters)
            rules.append(rule_dict)

        return {
            'name': condition.name,
            'description': condition.description,
            'rules': rules
        }

    def get_all(self) -> List[Condition]:
        """모든 조건 조회"""
        data = self._load_from_file()
        conditions = []

        for cond_data in data.get('conditions', []):
            try:
                condition = self._dict_to_condition(cond_data)
                conditions.append(condition)
            except Exception as e:
                console.print(f"[yellow]![/yellow] 조건 로드 실패: {cond_data.get('name', 'unknown')} - {str(e)}")

        return conditions

    def get_by_name(self, name: str) -> Optional[Condition]:
        """이름으로 조건 조회"""
        conditions = self.get_all()
        for condition in conditions:
            if condition.name == name:
                return condition
        return None

    def save(self, condition: Condition) -> bool:
        """조건 저장"""
        data = self._load_from_file()
        conditions = data.get('conditions', [])

        # 중복 확인
        for existing in conditions:
            if existing['name'] == condition.name:
                console.print(f"[yellow]![/yellow] 이미 존재하는 조건: {condition.name}")
                return False

        # 추가
        conditions.append(self._condition_to_dict(condition))
        data['conditions'] = conditions

        success = self._save_to_file(data)
        if success:
            console.print(f"[green]✓[/green] 조건 저장 완료: {condition.name}")
        return success

    def update(self, condition: Condition) -> bool:
        """조건 수정"""
        data = self._load_from_file()
        conditions = data.get('conditions', [])

        # 기존 조건 찾아서 수정
        found = False
        for i, existing in enumerate(conditions):
            if existing['name'] == condition.name:
                conditions[i] = self._condition_to_dict(condition)
                found = True
                break

        if not found:
            console.print(f"[red]✗[/red] 조건을 찾을 수 없음: {condition.name}")
            return False

        data['conditions'] = conditions
        success = self._save_to_file(data)
        if success:
            console.print(f"[green]✓[/green] 조건 수정 완료: {condition.name}")
        return success

    def delete(self, name: str) -> bool:
        """조건 삭제"""
        data = self._load_from_file()
        conditions = data.get('conditions', [])

        # 필터링
        new_conditions = [c for c in conditions if c['name'] != name]

        if len(new_conditions) == len(conditions):
            console.print(f"[red]✗[/red] 조건을 찾을 수 없음: {name}")
            return False

        data['conditions'] = new_conditions
        success = self._save_to_file(data)
        if success:
            console.print(f"[green]✓[/green] 조건 삭제 완료: {name}")
        return success

    def exists(self, name: str) -> bool:
        """조건 존재 여부 확인"""
        return self.get_by_name(name) is not None
