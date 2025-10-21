"""
Fix Block2/3/4 specific parameter names that were incorrectly modified

Block2/3/4 specific parameters should remain as:
- block2_entry_surge_rate (NOT block2_block1_entry_surge_rate)
- block2_entry_ma_period (NOT block2_block1_entry_ma_period)
etc.

Also fix DB field access:
- preset.block1_block2_entry_surge_rate -> preset.block2_entry_surge_rate
"""
from pathlib import Path

def fix_repository(file_path: Path):
    """Fix Block2/3/4 specific parameter names in repository"""
    print(f"\n[Processing] {file_path.name}")

    content = file_path.read_text(encoding='utf-8')
    original_content = content

    fixes = []

    # Fix Block2 parameters (function arguments)
    for field in ['entry_surge_rate', 'entry_ma_period', 'entry_high_above_ma',
                  'entry_max_deviation_ratio', 'entry_min_trading_value',
                  'entry_volume_high_months', 'entry_volume_spike_ratio',
                  'entry_price_high_months', 'exit_condition_type',
                  'exit_ma_period', 'cooldown_days']:
        # Fix function arguments
        old1 = f'block2_block1_{field}='
        new1 = f'block2_{field}='
        if old1 in content:
            content = content.replace(old1, new1)
            fixes.append(f"{old1} -> {new1}")

        old2 = f'block3_block1_{field}='
        new2 = f'block3_{field}='
        if old2 in content:
            content = content.replace(old2, new2)
            fixes.append(f"{old2} -> {new2}")

        old3 = f'block4_block1_{field}='
        new3 = f'block4_{field}='
        if old3 in content:
            content = content.replace(old3, new3)
            fixes.append(f"{old3} -> {new3}")

        # Fix DB field access: preset.block1_block2_* -> preset.block2_*
        old4 = f'preset.block1_block2_{field}'
        new4 = f'preset.block2_{field}'
        if old4 in content:
            content = content.replace(old4, new4)
            fixes.append(f"{old4} -> {new4}")

        old5 = f'preset.block1_block3_{field}'
        new5 = f'preset.block3_{field}'
        if old5 in content:
            content = content.replace(old5, new5)
            fixes.append(f"{old5} -> {new5}")

        old6 = f'preset.block1_block4_{field}'
        new6 = f'preset.block4_{field}'
        if old6 in content:
            content = content.replace(old6, new6)
            fixes.append(f"{old6} -> {new6}")

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"  [SUCCESS] Fixed {len(fixes)} issues")
        for fix in fixes[:5]:  # Show first 5
            print(f"    - {fix}")
        if len(fixes) > 5:
            print(f"    ... and {len(fixes) - 5} more")
    else:
        print(f"  [SKIP] No fixes needed")

    return len(fixes)

def main():
    """Fix both repository files"""
    print("=" * 80)
    print("Fix BlockN Specific Parameter Names")
    print("=" * 80)

    repo_dir = Path("src/infrastructure/repositories")

    files = [
        repo_dir / "seed_condition_preset_repository.py",
        repo_dir / "redetection_condition_preset_repository.py"
    ]

    total_fixes = 0

    for file_path in files:
        if file_path.exists():
            fixes = fix_repository(file_path)
            total_fixes += fixes
        else:
            print(f"\n[ERROR] File not found: {file_path}")

    print("\n" + "=" * 80)
    print(f"[SUCCESS] Fixed {total_fixes} total issues!")
    print("=" * 80)

if __name__ == '__main__':
    main()
