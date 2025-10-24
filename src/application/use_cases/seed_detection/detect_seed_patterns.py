"""
Detect Seed Patterns Use Case

High-quality seed pattern detection with strict conditions
"""
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.services.block_graph_loader import BlockGraphLoader
from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.domain.entities.patterns import SeedPattern, BlockFeatures
from src.domain.entities.conditions import ExpressionEngine
from src.infrastructure.repositories.stock.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.seed_pattern_repository_impl import SeedPatternRepositoryImpl


class DetectSeedPatternsUseCase:
    """
    Seed Pattern 자동 탐지 Use Case

    Clean Architecture Use Case layer
    Orchestrates seed pattern detection business logic
    """

    def __init__(self, db_path: str = "data/database/stock_data.db"):
        """
        Args:
            db_path: Database file path
        """
        self.db_path = db_path
        engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=engine)
        self.session = Session()

        self.stock_repo = SqliteStockRepository(db_path=db_path)
        self.seed_pattern_repo = SeedPatternRepositoryImpl(self.session)
        self.block_graph_loader = BlockGraphLoader()
        self.expression_engine = ExpressionEngine()

    def execute(
        self,
        yaml_path: str,
        ticker: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        max_patterns: int = 10
    ) -> List[SeedPattern]:
        """
        Execute seed pattern detection

        Seed patterns 탐지 및 저장

        Args:
            yaml_path: Seed detection YAML file path
            ticker: Stock ticker
            from_date: Start date
            to_date: End date
            max_patterns: Maximum number of seed patterns to save

        Returns:
            List of saved SeedPattern entities
        """
        print(f"\n{'='*60}")
        print(f"🌱 Seed Pattern Detection: {ticker}")
        print(f"{'='*60}")

        # Load seed detection graph
        print(f"📋 Loading seed graph: {yaml_path}")
        seed_graph = self.block_graph_loader.load_from_file(yaml_path)

        if seed_graph.pattern_type != "seed":
            raise ValueError(f"YAML must have pattern_type='seed', got '{seed_graph.pattern_type}'")

        # Load stock data
        print(f"📊 Loading stock data for {ticker}...")

        # Set default dates
        if from_date is None:
            from_date = date(2015, 1, 1)
        if to_date is None:
            to_date = date.today()

        stocks = self.stock_repo.get_stock_data(
            ticker=ticker,
            start_date=from_date,
            end_date=to_date
        )

        if not stocks:
            print(f"⚠️  No stock data found for {ticker}")
            return []

        print(f"   Found {len(stocks)} candles")

        # Detect blocks
        print(f"🔍 Detecting blocks with seed conditions...")
        detector = DynamicBlockDetector(seed_graph, self.expression_engine)
        detections = detector.detect_blocks(ticker, stocks)

        print(f"   Detected {len(detections)} blocks")

        # Group detections into patterns
        print(f"🔗 Grouping blocks into patterns...")
        patterns = self._group_detections_into_patterns(detections)

        print(f"   Found {len(patterns)} complete patterns")

        # Convert to SeedPattern entities
        print(f"💾 Converting to SeedPattern entities...")
        seed_patterns = []

        for idx, pattern_blocks in enumerate(patterns[:max_patterns]):
            pattern_name = f"seed_{ticker}_{datetime.now().strftime('%Y%m%d')}_{idx+1:03d}"

            try:
                seed_pattern = self._create_seed_pattern(
                    pattern_name=pattern_name,
                    ticker=ticker,
                    yaml_path=yaml_path,
                    blocks=pattern_blocks
                )

                # Save to DB
                saved = self.seed_pattern_repo.save(seed_pattern)
                seed_patterns.append(saved)

                print(f"   ✅ Saved: {pattern_name} (ID={saved.id})")

            except Exception as e:
                print(f"   ❌ Failed to save pattern {idx+1}: {e}")
                continue

        # Commit all changes to database
        self.session.commit()

        print(f"\n✅ Successfully saved {len(seed_patterns)} seed patterns")
        return seed_patterns

    def _group_detections_into_patterns(
        self,
        detections: List,
        max_gap_days: int = 30
    ) -> List[List]:
        """
        Detections을 pattern으로 그룹화

        Args:
            detections: Block detections
            max_gap_days: Maximum gap between blocks in same pattern

        Returns:
            List of pattern groups (each is a list of blocks)
        """
        if not detections:
            return []

        # Sort by started_at
        sorted_detections = sorted(detections, key=lambda d: d.started_at or date.min)

        patterns = []
        current_pattern = [sorted_detections[0]]

        for detection in sorted_detections[1:]:
            last_detection = current_pattern[-1]

            if detection.started_at and last_detection.started_at:
                gap = (detection.started_at - last_detection.started_at).days

                if gap <= max_gap_days:
                    current_pattern.append(detection)
                else:
                    # Start new pattern
                    if len(current_pattern) >= 2:  # At least 2 blocks
                        patterns.append(current_pattern)
                    current_pattern = [detection]

        # Add last pattern
        if len(current_pattern) >= 2:
            patterns.append(current_pattern)

        return patterns

    def _create_seed_pattern(
        self,
        pattern_name: str,
        ticker: str,
        yaml_path: str,
        blocks: List
    ) -> SeedPattern:
        """
        Create SeedPattern entity from detections

        Args:
            pattern_name: Pattern name
            ticker: Stock ticker
            yaml_path: YAML config path
            blocks: List of block detections

        Returns:
            SeedPattern entity
        """
        # Extract block features
        block_features = []
        prices = []
        volumes = []

        for block in blocks:
            # Calculate duration from started_at and ended_at
            duration = 0
            if block.started_at and block.ended_at:
                duration = (block.ended_at - block.started_at).days + 1

            feature = BlockFeatures(
                block_id=block.block_id,
                block_type=block.block_type,
                started_at=block.started_at,
                ended_at=block.ended_at,
                duration_candles=duration,
                low_price=block.peak_price or 0.0,  # Use peak_price as approximation
                high_price=block.peak_price or 0.0,  # Use peak_price as approximation
                peak_price=block.peak_price or 0.0,
                peak_date=block.peak_date or block.started_at,
                min_volume=block.peak_volume or 0,  # Use peak_volume as approximation
                max_volume=block.peak_volume or 0,  # Use peak_volume as approximation
                peak_volume=block.peak_volume or 0,
                avg_volume=block.peak_volume or 0  # Use peak_volume as approximation
            )
            block_features.append(feature)

            if block.peak_price:
                prices.append(block.peak_price)
            if block.peak_volume:
                volumes.append(float(block.peak_volume))

        # Normalize shapes
        price_shape = SeedPattern.normalize_sequence(prices) if prices else []
        volume_shape = SeedPattern.normalize_sequence(volumes) if volumes else []

        # Create SeedPattern
        return SeedPattern(
            pattern_name=pattern_name,
            ticker=ticker,
            yaml_config_path=yaml_path,
            detection_date=blocks[0].started_at or date.today(),
            block_features=block_features,
            price_shape=price_shape,
            volume_shape=volume_shape
        )
