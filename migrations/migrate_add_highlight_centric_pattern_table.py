"""
Migration: Add highlight_centric_pattern table

Date: 2025-10-27
Purpose: Create table for storing highlight-centric detection patterns
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.infrastructure.database.models import HighlightCentricPatternModel
from src.infrastructure.database.connection import get_db_connection

import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def migrate():
    """
    Create highlight_centric_pattern table.

    Migration Steps:
    1. Connect to database
    2. Check if table already exists
    3. Create table with indexes
    4. Verify table creation
    """

    # Get database connection
    db_path = "data/database/stock_data.db"
    logger.info(f"Connecting to database: {db_path}")

    db_connection = get_db_connection(db_path)
    engine = db_connection.engine

    try:
        # Step 1: Check if table already exists
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='highlight_centric_pattern'"
            ))
            existing = result.fetchone()

            if existing:
                logger.warning("Table 'highlight_centric_pattern' already exists")
                response = input("Drop and recreate table? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Migration aborted")
                    return

                # Drop existing table
                logger.info("Dropping existing table...")
                conn.execute(text("DROP TABLE highlight_centric_pattern"))
                conn.commit()
                logger.info("Table dropped")

        # Step 2: Create table
        logger.info("Creating highlight_centric_pattern table...")

        # Create only the new table (not all tables)
        HighlightCentricPatternModel.__table__.create(engine, checkfirst=True)

        logger.info("✅ Table created successfully")

        # Step 3: Verify table structure
        with engine.connect() as conn:
            result = conn.execute(text(
                "PRAGMA table_info(highlight_centric_pattern)"
            ))
            columns = result.fetchall()

            logger.info("\nTable structure:")
            logger.info("Columns:")
            for col in columns:
                logger.info(f"  - {col[1]} ({col[2]})")

            # Check indexes
            result = conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='highlight_centric_pattern'"
            ))
            indexes = result.fetchall()

            logger.info("\nIndexes:")
            for idx in indexes:
                logger.info(f"  - {idx[0]}")

        logger.info("\n✅ Migration completed successfully")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise

    finally:
        engine.dispose()


if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("Migration: Add highlight_centric_pattern table")
    logger.info("=" * 70)

    try:
        migrate()
    except KeyboardInterrupt:
        logger.info("\nMigration interrupted by user")
    except Exception as e:
        logger.error(f"\nMigration failed: {e}")
        sys.exit(1)
