"""
Update field names in repository files: entry_* -> block1_entry_*

Updates both seed_condition_preset_repository.py and redetection_condition_preset_repository.py
"""
import re
from pathlib import Path

# Field mappings
FIELD_MAPPINGS = {
    'preset.entry_surge_rate': 'preset.block1_entry_surge_rate',
    'preset.entry_ma_period': 'preset.block1_entry_ma_period',
    'preset.entry_high_above_ma': 'preset.block1_entry_high_above_ma',
    'preset.entry_max_deviation_ratio': 'preset.block1_entry_max_deviation_ratio',
    'preset.entry_min_trading_value': 'preset.block1_entry_min_trading_value',
    'preset.entry_volume_high_months': 'preset.block1_entry_volume_high_months',
    'preset.entry_volume_spike_ratio': 'preset.block1_entry_volume_spike_ratio',
    'preset.entry_price_high_months': 'preset.block1_entry_price_high_months',
    'preset.exit_condition_type': 'preset.block1_exit_condition_type',
    'preset.exit_ma_period': 'preset.block1_exit_ma_period',
    'preset.cooldown_days': 'preset.block1_cooldown_days',

    # Also for condition.* patterns (in save())
    'condition.entry_surge_rate': 'condition.base.block1_entry_surge_rate',
    'condition.entry_ma_period': 'condition.base.block1_entry_ma_period',
    'condition.entry_high_above_ma': 'condition.base.block1_entry_high_above_ma',
    'condition.entry_max_deviation_ratio': 'condition.base.block1_entry_max_deviation_ratio',
    'condition.entry_min_trading_value': 'condition.base.block1_entry_min_trading_value',
    'condition.entry_volume_high_months': 'condition.base.block1_entry_volume_high_months',
    'condition.entry_volume_spike_ratio': 'condition.base.block1_entry_volume_spike_ratio',
    'condition.entry_price_high_months': 'condition.base.block1_entry_price_high_months',
    'condition.exit_condition_type': 'condition.base.block1_exit_condition_type',
    'condition.exit_ma_period': 'condition.base.block1_exit_ma_period',
    'condition.cooldown_days': 'condition.base.block1_cooldown_days',
}

# BaseEntryCondition field mappings (without condition./preset. prefix)
BASE_ENTRY_MAPPINGS = {
    'entry_surge_rate=preset.': 'block1_entry_surge_rate=preset.block1_',
    'entry_ma_period=preset.': 'block1_entry_ma_period=preset.block1_',
    'entry_high_above_ma=': 'block1_entry_high_above_ma=',
    'entry_max_deviation_ratio=preset.': 'block1_entry_max_deviation_ratio=preset.block1_',
    'entry_min_trading_value=preset.': 'block1_entry_min_trading_value=preset.block1_',
    'entry_volume_high_months=preset.': 'block1_entry_volume_high_months=preset.block1_',
    'entry_volume_spike_ratio=preset.': 'block1_entry_volume_spike_ratio=preset.block1_',
    'entry_price_high_months=preset.': 'block1_entry_price_high_months=preset.block1_',
    'exit_condition_type=Block1ExitConditionType(preset.': 'block1_exit_condition_type=Block1ExitConditionType(preset.block1_',
    'exit_ma_period=preset.': 'block1_exit_ma_period=preset.block1_',
    'cooldown_days=preset.': 'block1_cooldown_days=preset.block1_',
}

def update_file(file_path: Path):
    """Update field names in a repository file"""
    print(f"\n[Processing] {file_path.name}")

    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # Apply field mappings
    for old, new in FIELD_MAPPINGS.items():
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            print(f"  [OK] {old} -> {new} ({count} occurrences)")

    # Apply BaseEntryCondition construction patterns
    for old, new in BASE_ENTRY_MAPPINGS.items():
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            print(f"  [OK] BaseEntryCondition: {old[:30]}... -> {new[:30]}... ({count} occurrences)")

    # Write back
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"  [SUCCESS] Updated {file_path.name}")
    else:
        print(f"  [SKIP] No changes needed")

def main():
    """Update both repository files"""
    print("=" * 80)
    print("Update Repository Field Names: entry_* -> block1_*")
    print("=" * 80)

    repo_dir = Path("src/infrastructure/repositories")

    files = [
        repo_dir / "seed_condition_preset_repository.py",
        repo_dir / "redetection_condition_preset_repository.py"
    ]

    for file_path in files:
        if file_path.exists():
            update_file(file_path)
        else:
            print(f"\n[ERROR] File not found: {file_path}")

    print("\n" + "=" * 80)
    print("[SUCCESS] Field name update completed!")
    print("=" * 80)

if __name__ == '__main__':
    main()
