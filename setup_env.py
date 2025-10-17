"""
환경 설정 및 DB 초기화 스크립트

사용법:
    python setup_env.py
"""

import sys
import subprocess
from pathlib import Path

def check_packages():
    """필요한 패키지 확인"""
    required = {
        'sqlalchemy': 'SQLAlchemy>=2.0.0',
        'pandas': 'pandas>=2.0.0',
        'requests': 'requests>=2.28.0',
        'bs4': 'beautifulsoup4>=4.12.0',  # 네이버 금융 크롤링
        'lxml': 'lxml>=4.9.0',  # HTML 파싱
        'html5lib': 'html5lib>=1.1'  # pandas HTML 파싱
    }

    missing = []

    for package, version in required.items():
        try:
            __import__(package)
            print(f"[OK] {package}")
        except ImportError:
            print(f"[MISSING] {package}")
            missing.append(version)

    return missing

def install_packages(missing):
    """패키지 설치"""
    if not missing:
        print("\n[INFO] All packages installed!")
        return True

    print(f"\n{len(missing)} packages need to be installed:")
    for pkg in missing:
        print(f"  - {pkg}")

    response = input("\nInstall? (y/N): ")
    if response.lower() != 'y':
        print("Installation cancelled.")
        return False

    try:
        # pip 설치 시도
        print("\nInstalling packages via pip...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
        print("\n[SUCCESS] Package installation complete!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Package installation failed: {e}")
        print("\nManual installation:")
        print(f"  python -m pip install {' '.join(missing)}")
        return False

def create_database():
    """데이터베이스 생성"""
    try:
        from src.infrastructure.database.connection import DatabaseConnection

        db_path = Path('data/database/stock_data.db')
        db_path.parent.mkdir(parents=True, exist_ok=True)

        print("\nDB 초기화 중...")
        db = DatabaseConnection(str(db_path))
        db.create_tables()

        print(f"[SUCCESS] DB created: {db_path}")

        # 테이블 확인
        print("\nCreated tables:")
        from src.infrastructure.database.models import Base
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")

        return True

    except Exception as e:
        print(f"\n[ERROR] DB creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("POTALE_STOCK Environment Setup")
    print("=" * 60)

    # 1. 패키지 확인
    print("\n[1/2] Checking required packages...")
    missing = check_packages()

    if missing:
        success = install_packages(missing)
        if not success:
            print("\n[ERROR] Please install required packages first.")
            sys.exit(1)

    # 2. DB 생성
    print("\n[2/2] Initializing database...")
    success = create_database()

    if success:
        print("\n" + "=" * 60)
        print("[SUCCESS] Environment setup complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Small test: python bulk_collect.py --tickers 005930,000660,035720 --from 2024-09-17")
        print("  2. Full collect: python bulk_collect.py --all --from 2020-01-01 --investor")
    else:
        print("\n[ERROR] Environment setup failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
