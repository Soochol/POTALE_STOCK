"""
Update field names in service files: condition.base.entry_* -> condition.base.block1_entry_*

Updates checker and detector files
"""
from pathlib import Path

# Field mappings for condition.base.* access
CONDITION_BASE_MAPPINGS = {
    'condition.base.entry_surge_rate': 'condition.base.block1_entry_surge_rate',
    'condition.base.entry_ma_period': 'condition.base.block1_entry_ma_period',
    'condition.base.entry_high_above_ma': 'condition.base.block1_entry_high_above_ma',
    'condition.base.entry_max_deviation_ratio': 'condition.base.block1_entry_max_deviation_ratio',
    'condition.base.entry_min_trading_value': 'condition.base.block1_entry_min_trading_value',
    'condition.base.entry_volume_high_months': 'condition.base.block1_entry_volume_high_months',
    'condition.base.entry_volume_spike_ratio': 'condition.base.block1_entry_volume_spike_ratio',
    'condition.base.entry_price_high_months': 'condition.base.block1_entry_price_high_months',
    'condition.base.exit_condition_type': 'condition.base.block1_exit_condition_type',
    'condition.base.exit_ma_period': 'condition.base.block1_exit_ma_period',
    'condition.base.cooldown_days': 'condition.base.block1_cooldown_days',
}

# BaseEntryCondition field names (in constructors, etc.)
BASE_ENTRY_CONSTRUCTION = {
    'entry_surge_rate=getattr(condition, ': 'block1_entry_surge_rate=getattr(condition, ',
    'entry_ma_period=getattr(condition, ': 'block1_entry_ma_period=getattr(condition, ',
    'entry_high_above_ma=getattr(condition, ': 'block1_entry_high_above_ma=getattr(condition, ',
    'entry_max_deviation_ratio=getattr(condition, ': 'block1_entry_max_deviation_ratio=getattr(condition, ',
    'entry_min_trading_value=getattr(condition, ': 'block1_entry_min_trading_value=getattr(condition, ',
    'entry_volume_high_months=getattr(condition, ': 'block1_entry_volume_high_months=getattr(condition, ',
    'entry_volume_spike_ratio=getattr(condition, ': 'block1_entry_volume_spike_ratio=getattr(condition, ',
    'entry_price_high_months=getattr(condition, ': 'block1_entry_price_high_months=getattr(condition, ',
    'exit_condition_type=getattr(condition, ': 'block1_exit_condition_type=getattr(condition, ',
    'exit_ma_period=getattr(condition, ': 'block1_exit_ma_period=getattr(condition, ',
    'cooldown_days=getattr(condition, ': 'block1_cooldown_days=getattr(condition, ',

    # Fallback to condition.base.* patterns
    '.block1_entry_surge_rate) if getattr(condition, ': '.block1_entry_surge_rate) if getattr(condition, ',
    '.block1_entry_ma_period) if getattr(condition, ': '.block1_entry_ma_period) if getattr(condition, ',
    '.block1_entry_high_above_ma) if getattr(condition, ': '.block1_entry_high_above_ma) if getattr(condition, ',
    '.block1_entry_max_deviation_ratio) if getattr(condition, ': '.block1_entry_max_deviation_ratio) if getattr(condition, ',
    '.block1_entry_min_trading_value) if getattr(condition, ': '.block1_entry_min_trading_value) if getattr(condition, ',
    '.block1_entry_volume_high_months) if getattr(condition, ': '.block1_entry_volume_high_months) if getattr(condition, ',
    '.block1_entry_volume_spike_ratio) if getattr(condition, ': '.block1_entry_volume_spike_ratio) if getattr(condition, ',
    '.block1_entry_price_high_months) if getattr(condition, ': '.block1_entry_price_high_months) if getattr(condition, ',
    '.block1_exit_condition_type) if getattr(condition, ': '.block1_exit_condition_type) if getattr(condition, ',
    '.block1_exit_ma_period) if getattr(condition, ': '.block1_exit_ma_period) if getattr(condition, ',
    '.block1_cooldown_days) if getattr(condition, ': '.block1_cooldown_days) if getattr(condition, ',

    # else condition.base.* patterns
    'else condition.base.entry_surge_rate': 'else condition.base.block1_entry_surge_rate',
    'else condition.base.entry_ma_period': 'else condition.base.block1_entry_ma_period',
    'else condition.base.entry_high_above_ma': 'else condition.base.block1_entry_high_above_ma',
    'else condition.base.entry_max_deviation_ratio': 'else condition.base.block1_entry_max_deviation_ratio',
    'else condition.base.entry_min_trading_value': 'else condition.base.block1_entry_min_trading_value',
    'else condition.base.entry_volume_high_months': 'else condition.base.block1_entry_volume_high_months',
    'else condition.base.entry_volume_spike_ratio': 'else condition.base.block1_entry_volume_spike_ratio',
    'else condition.base.entry_price_high_months': 'else condition.base.block1_entry_price_high_months',
    'else condition.base.exit_condition_type': 'else condition.base.block1_exit_condition_type',
    'else condition.base.exit_ma_period': 'else condition.base.block1_exit_ma_period',
    'else condition.base.cooldown_days': 'else condition.base.block1_cooldown_days',
}

def update_file(file_path: Path):
    """Update field names in a service file"""
    print(f"\n[Processing] {file_path.name}")

    content = file_path.read_text(encoding='utf-8')
    original_content = content
    total_changes = 0

    # Apply condition.base.* mappings first
    for old, new in CONDITION_BASE_MAPPINGS.items():
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            total_changes += count
            print(f"  [OK] {old} -> {new} ({count} occurrences)")

    # Apply BaseEntryCondition construction patterns
    for old, new in BASE_ENTRY_CONSTRUCTION.items():
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            total_changes += count
            print(f"  [OK] {old[:40]}... -> {new[:40]}... ({count} occurrences)")

    # Write back
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"  [SUCCESS] Updated {file_path.name} ({total_changes} total changes)")
    else:
        print(f"  [SKIP] No changes needed")

    return total_changes

def main():
    """Update all service files"""
    print("=" * 80)
    print("Update Service Field Names: entry_* -> block1_*")
    print("=" * 80)

    service_dir = Path("src/application/services")

    files = [
        service_dir / "block1_checker.py",
        service_dir / "block2_checker.py",
        service_dir / "block3_checker.py",
        service_dir / "block4_checker.py",
        service_dir / "pattern_seed_detector.py",
        service_dir / "pattern_redetector.py",
    ]

    total_files = 0
    total_changes = 0

    for file_path in files:
        if file_path.exists():
            changes = update_file(file_path)
            if changes > 0:
                total_files += 1
                total_changes += changes
        else:
            print(f"\n[ERROR] File not found: {file_path}")

    print("\n" + "=" * 80)
    print(f"[SUCCESS] Updated {total_files} files with {total_changes} total changes!")
    print("=" * 80)

if __name__ == '__main__':
    main()
