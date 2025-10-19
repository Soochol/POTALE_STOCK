"""
Update field names in test files: entry_* -> block1_entry_*
"""
from pathlib import Path

# BaseEntryCondition constructor parameter mappings
CONSTRUCTOR_MAPPINGS = {
    'entry_surge_rate=': 'block1_entry_surge_rate=',
    'entry_ma_period=': 'block1_entry_ma_period=',
    'entry_high_above_ma=': 'block1_entry_high_above_ma=',
    'entry_max_deviation_ratio=': 'block1_entry_max_deviation_ratio=',
    'entry_min_trading_value=': 'block1_entry_min_trading_value=',
    'entry_volume_high_months=': 'block1_entry_volume_high_months=',
    'entry_volume_spike_ratio=': 'block1_entry_volume_spike_ratio=',
    'entry_price_high_months=': 'block1_entry_price_high_months=',
    'exit_condition_type=': 'block1_exit_condition_type=',
    'exit_ma_period=': 'block1_exit_ma_period=',
    'cooldown_days=': 'block1_cooldown_days=',
}

# Field access patterns (base.entry_* -> base.block1_entry_*)
ACCESS_MAPPINGS = {
    'base.entry_surge_rate': 'base.block1_entry_surge_rate',
    'base.entry_ma_period': 'base.block1_entry_ma_period',
    'base.entry_high_above_ma': 'base.block1_entry_high_above_ma',
    'base.entry_max_deviation_ratio': 'base.block1_entry_max_deviation_ratio',
    'base.entry_min_trading_value': 'base.block1_entry_min_trading_value',
    'base.entry_volume_high_months': 'base.block1_entry_volume_high_months',
    'base.entry_volume_spike_ratio': 'base.block1_entry_volume_spike_ratio',
    'base.entry_price_high_months': 'base.block1_entry_price_high_months',
    'base.exit_condition_type': 'base.block1_exit_condition_type',
    'base.exit_ma_period': 'base.block1_exit_ma_period',
    'base.cooldown_days': 'base.block1_cooldown_days',
}

def update_file(file_path: Path):
    """Update field names in a test file"""
    print(f"\n[Processing] {file_path.name}")

    content = file_path.read_text(encoding='utf-8')
    original_content = content
    total_changes = 0

    # Apply constructor parameter mappings
    for old, new in CONSTRUCTOR_MAPPINGS.items():
        # Only replace in BaseEntryCondition context (check for common patterns)
        # We need to be careful not to replace in comments or strings
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            total_changes += count
            print(f"  [OK] {old} -> {new} ({count} occurrences)")

    # Apply field access mappings
    for old, new in ACCESS_MAPPINGS.items():
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            total_changes += count
            print(f"  [OK] {old} -> {new} ({count} occurrences)")

    # Write back
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"  [SUCCESS] Updated {file_path.name} ({total_changes} total changes)")
    else:
        print(f"  [SKIP] No changes needed")

    return total_changes

def main():
    """Update test files"""
    print("=" * 80)
    print("Update Test Field Names: entry_* -> block1_*")
    print("=" * 80)

    test_files = [
        Path("test_refactored_block1.py"),
        Path("test_block_specific_params.py"),
    ]

    total_files = 0
    total_changes = 0

    for file_path in test_files:
        if file_path.exists():
            changes = update_file(file_path)
            if changes > 0:
                total_files += 1
                total_changes += changes
        else:
            print(f"\n[WARNING] File not found: {file_path}")

    print("\n" + "=" * 80)
    if total_changes > 0:
        print(f"[SUCCESS] Updated {total_files} files with {total_changes} total changes!")
    else:
        print("[INFO] No changes needed")
    print("=" * 80)

if __name__ == '__main__':
    main()
