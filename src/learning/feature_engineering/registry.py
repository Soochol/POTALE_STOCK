"""
Feature Registry System

This module provides a registry pattern for managing feature extraction functions.
Features can be registered, enabled/disabled, and extracted dynamically based on
configuration files.
"""
from typing import Dict, List, Callable, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, field


@dataclass
class FeatureMetadata:
    """Metadata for a registered feature"""
    name: str
    func: Callable
    category: str
    description: str = ""
    requires: List[str] = field(default_factory=list)  # Required context keys
    enabled: bool = True
    version: str = "1.0"


class FeatureRegistry:
    """
    Registry for feature extraction functions

    Features are registered using a decorator pattern and can be
    dynamically enabled/disabled via configuration.

    Example:
        >>> registry = FeatureRegistry()
        >>>
        >>> @registry.register('price_rsi', category='technical')
        >>> def calculate_rsi(df, period=14):
        >>>     return calculate_rsi_indicator(df['close'], period)
        >>>
        >>> features = registry.extract(['price_rsi'], df)
    """

    def __init__(self):
        self._features: Dict[str, FeatureMetadata] = {}

    def register(
        self,
        name: str,
        category: str,
        description: str = "",
        requires: List[str] = None,
        version: str = "1.0"
    ):
        """
        Decorator to register a feature function

        Args:
            name: Feature name (used in configuration)
            category: Feature category (price, volume, technical, etc.)
            description: Human-readable description
            requires: List of required context keys (e.g., ['block1_high'])
            version: Feature version for tracking changes
        """
        def decorator(func: Callable):
            self._features[name] = FeatureMetadata(
                name=name,
                func=func,
                category=category,
                description=description,
                requires=requires or [],
                enabled=True,
                version=version
            )
            return func
        return decorator

    def list_features(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[str]:
        """
        List registered features

        Args:
            category: Filter by category (None = all)
            enabled_only: Only show enabled features

        Returns:
            List of feature names
        """
        features = []
        for name, meta in self._features.items():
            if enabled_only and not meta.enabled:
                continue
            if category and meta.category != category:
                continue
            features.append(name)
        return sorted(features)

    def get_metadata(self, name: str) -> FeatureMetadata:
        """Get metadata for a feature"""
        if name not in self._features:
            raise ValueError(f"Unknown feature: {name}")
        return self._features[name]

    def enable(self, name: str):
        """Enable a feature"""
        if name not in self._features:
            raise ValueError(f"Unknown feature: {name}")
        self._features[name].enabled = True

    def disable(self, name: str):
        """Disable a feature"""
        if name not in self._features:
            raise ValueError(f"Unknown feature: {name}")
        self._features[name].enabled = False

    def extract(
        self,
        names: List[str],
        df: pd.DataFrame,
        context: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Extract selected features from data

        Args:
            names: List of feature names to extract
            df: Input dataframe with OHLCV data
            context: Additional context (e.g., block1 info for block2 features)

        Returns:
            DataFrame with extracted features
        """
        if context is None:
            context = {}

        results = {}

        for name in names:
            if name not in self._features:
                raise ValueError(f"Unknown feature: {name}")

            meta = self._features[name]

            if not meta.enabled:
                raise ValueError(f"Feature '{name}' is disabled")

            # Check required context
            for req in meta.requires:
                if req not in context:
                    raise ValueError(
                        f"Feature '{name}' requires context key '{req}'"
                    )

            # Extract feature
            try:
                if meta.requires:
                    # Pass context as kwargs
                    feature_data = meta.func(df, **{k: context[k] for k in meta.requires})
                else:
                    feature_data = meta.func(df)

                results[name] = feature_data

            except Exception as e:
                raise RuntimeError(
                    f"Failed to extract feature '{name}': {e}"
                ) from e

        return pd.DataFrame(results, index=df.index)

    def get_categories(self) -> List[str]:
        """Get all feature categories"""
        categories = set(meta.category for meta in self._features.values())
        return sorted(categories)

    def get_features_by_category(self) -> Dict[str, List[str]]:
        """Get features grouped by category"""
        result = {}
        for name, meta in self._features.items():
            if meta.category not in result:
                result[meta.category] = []
            result[meta.category].append(name)

        # Sort each category
        for category in result:
            result[category].sort()

        return result

    def print_summary(self):
        """Print a summary of registered features"""
        categories = self.get_features_by_category()

        print(f"\nFeature Registry Summary")
        print(f"{'='*60}")
        print(f"Total features: {len(self._features)}")
        print(f"Categories: {len(categories)}")
        print()

        for category in sorted(categories.keys()):
            features = categories[category]
            print(f"[{category.upper()}] ({len(features)} features)")
            for name in features:
                meta = self.get_metadata(name)
                status = "ENABLED" if meta.enabled else "DISABLED"
                print(f"  - {name:30} [{status}]")
                if meta.description:
                    print(f"    {meta.description}")
            print()


# Global registry instance
feature_registry = FeatureRegistry()
