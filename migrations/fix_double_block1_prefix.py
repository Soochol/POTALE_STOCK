"""
Fix double block1_ prefix issue: preset.block1_block1_* -> preset.block1_*
"""
from pathlib import Path

def fix_file(file_path: Path):
    """Fix double block1_ prefix in a file"""
    print(f"\n[Processing] {file_path.name}")

    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # Fix double prefix
    content = content.replace('preset.block1_block1_', 'preset.block1_')

    # Count fixes
    fixes = original_content.count('preset.block1_block1_')

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"  [SUCCESS] Fixed {fixes} double prefixes")
    else:
        print(f"  [SKIP] No fixes needed")

    return fixes

def main():
    """Fix both repository files"""
    print("=" * 80)
    print("Fix Double block1_ Prefix")
    print("=" * 80)

    repo_dir = Path("src/infrastructure/repositories")

    files = [
        repo_dir / "seed_condition_preset_repository.py",
        repo_dir / "redetection_condition_preset_repository.py"
    ]

    total_fixes = 0

    for file_path in files:
        if file_path.exists():
            fixes = fix_file(file_path)
            total_fixes += fixes
        else:
            print(f"\n[ERROR] File not found: {file_path}")

    print("\n" + "=" * 80)
    print(f"[SUCCESS] Fixed {total_fixes} total double prefixes!")
    print("=" * 80)

if __name__ == '__main__':
    main()
