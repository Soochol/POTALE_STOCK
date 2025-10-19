"""
Database Connection Manager
SQLite 데이터베이스 연결 관리
"""
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from rich.console import Console

console = Console()


class DatabaseConnection:
    """데이터베이스 연결 관리 클래스"""

    def __init__(self, db_path: str = "data/database/stock_data.db"):
        """
        Args:
            db_path: 데이터베이스 파일 경로 또는 connection string
        """
        # connection string인지 확인
        if db_path.startswith("sqlite:///"):
            self.connection_string = db_path
            # connection string에서 실제 파일 경로 추출
            file_path = db_path.replace("sqlite:///", "")
            self.db_path = Path(file_path)
        else:
            self.db_path = Path(db_path)
            self.connection_string = f"sqlite:///{self.db_path}"

        # 디렉토리 생성
        if self.db_path.parent != Path('.'):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 엔진 생성
        self.engine = create_engine(
            self.connection_string,
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            echo=False  # True로 설정하면 SQL 로그 출력
        )

        # SQLite 최적화 설정
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache (negative = KB)
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
            cursor.execute("PRAGMA page_size=4096")  # Optimal page size
            cursor.close()

        # 세션 팩토리
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        print(f"Database initialized: {self.db_path}")

    def create_tables(self):
        """모든 테이블 생성"""
        from .models import Base
        Base.metadata.create_all(bind=self.engine)
        print("Database tables created")

    def drop_tables(self):
        """모든 테이블 삭제"""
        from .models import Base
        Base.metadata.drop_all(bind=self.engine)
        print("Database tables dropped")

    def get_session(self) -> Session:
        """새로운 세션 반환"""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        세션 컨텍스트 매니저

        Usage:
            with db_connection.session_scope() as session:
                session.query(...)
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """데이터베이스 연결 종료"""
        if hasattr(self, 'engine') and self.engine:
            self.engine.dispose()
            print("Database connection closed")


# 전역 데이터베이스 연결 인스턴스
_db_connection: DatabaseConnection = None


def get_db_connection(db_path: str = "data/database/stock_data.db") -> DatabaseConnection:
    """전역 데이터베이스 연결 인스턴스 반환"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection(db_path)
        _db_connection.create_tables()
    return _db_connection


@contextmanager
def get_db_session(db_path: str = "data/database/stock_data.db") -> Generator[Session, None, None]:
    """
    데이터베이스 세션 컨텍스트 매니저 (편의 함수)

    Usage:
        with get_db_session() as session:
            session.query(...)
    """
    db = get_db_connection(db_path)
    with db.session_scope() as session:
        yield session
