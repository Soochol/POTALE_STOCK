"""
Block1 파라미터 이름 일괄 변경 스크립트
"""
import os
import re

# 파라미터 변경 매핑
PARAM_MAPPING = {
    'rate_threshold': 'entry_surge_rate',
    'ma_period': 'entry_ma_period',
    'deviation_threshold': 'max_deviation_ratio',
    'trading_value_threshold': 'min_trading_value',
    'volume_months': 'volume_high_months',
    'prev_day_volume_increase_ratio': 'volume_spike_ratio',
    'new_high_months': 'price_high_months',
}

# 변경할 파일 목록
FILES_TO_UPDATE = [
    'src/domain/entities/block1_condition.py',
    'src/application/services/block1_checker.py',
    'src/application/services/block1_indicator_calculator.py',
    'src/infrastructure/database/models.py',
    'src/infrastructure/repositories/block1_condition_preset_repository.py',
    'save_conditions.py',
    'detect_with_preset.py',
    'test_block1_custom_conditions.py',
    'test_block1_proper_conditions.py',
]

def replace_in_file(file_path: str, mappings: dict) -> int:
    """파일 내용에서 파라미터 이름 변경"""
    if not os.path.exists(file_path):
        print(f"  [SKIP] {file_path} - 파일 없음")
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes = 0

    for old_name, new_name in mappings.items():
        # self.old_name 패턴
        pattern1 = rf'\bself\.{old_name}\b'
        if re.search(pattern1, content):
            content = re.sub(pattern1, f'self.{new_name}', content)
            changes += len(re.findall(pattern1, original_content))

        # old_name= 패턴 (파라미터 할당)
        pattern2 = rf'\b{old_name}='
        if re.search(pattern2, content):
            content = re.sub(pattern2, f'{new_name}=', content)
            changes += len(re.findall(pattern2, original_content))

        # condition.old_name 패턴
        pattern3 = rf'\bcondition\.{old_name}\b'
        if re.search(pattern3, content):
            content = re.sub(pattern3, f'condition.{new_name}', content)
            changes += len(re.findall(pattern3, original_content))

        # preset.old_name 패턴
        pattern4 = rf'\bpreset\.{old_name}\b'
        if re.search(pattern4, content):
            content = re.sub(pattern4, f'preset.{new_name}', content)
            changes += len(re.findall(pattern4, original_content))

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] {file_path} - {changes} changes")
        return changes
    else:
        print(f"  [NO CHANGE] {file_path}")
        return 0

def main():
    print("="*70)
    print("Block1 파라미터 이름 일괄 변경")
    print("="*70)
    print()

    print("변경 매핑:")
    for old, new in PARAM_MAPPING.items():
        print(f"  {old:35s} → {new}")
    print()

    print("="*70)
    print("파일 업데이트 시작")
    print("="*70)
    print()

    total_changes = 0
    for file_path in FILES_TO_UPDATE:
        changes = replace_in_file(file_path, PARAM_MAPPING)
        total_changes += changes

    print()
    print("="*70)
    print(f"완료: 총 {total_changes}개 변경")
    print("="*70)

if __name__ == "__main__":
    main()
