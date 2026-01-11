"""
Email Analysis Module (H-4 Consolidation)
==========================================

Canonical analysis implementation using modular architecture.

The `DailyEmailAnalyzer` class is the recommended entry point for all
email analysis operations. Legacy classes are maintained for backward
compatibility but issue deprecation warnings.

Usage:
    from gmail_assistant.analysis import DailyEmailAnalyzer

    analyzer = DailyEmailAnalyzer(config_path)
    results = analyzer.analyze_emails(df)
"""

import warnings

# H-4: Canonical implementation from daily_email_analyzer.py
from .daily_email_analyzer import (
    ContentAnalyzer,
    DailyEmailAnalyzer,
    DataQualityAssessment,
    HierarchicalClassifier,
    InsightsGenerator,
    SenderAnalyzer,
    TemporalAnalyzer,
)

# Data converter (no duplicate)
from .email_data_converter import EmailDataConverter


# H-4: Legacy aliases with deprecation warnings
def _get_deprecated_email_analysis_engine():
    """Lazy import with deprecation warning for EmailAnalysisEngine."""
    warnings.warn(
        "EmailAnalysisEngine from daily_email_analysis is deprecated. "
        "Use DailyEmailAnalyzer from gmail_assistant.analysis instead.",
        DeprecationWarning,
        stacklevel=3
    )
    from .daily_email_analysis import EmailAnalysisEngine
    return EmailAnalysisEngine


def _get_deprecated_email_analyzer():
    """Lazy import with deprecation warning for EmailAnalyzer."""
    warnings.warn(
        "EmailAnalyzer from email_analyzer is deprecated. "
        "Use DailyEmailAnalyzer from gmail_assistant.analysis instead.",
        DeprecationWarning,
        stacklevel=3
    )
    from .email_analyzer import EmailAnalysisEngine as EmailAnalyzer
    return EmailAnalyzer


class _DeprecatedEmailAnalysisEngine:
    """Wrapper that issues deprecation warning on instantiation."""

    _real_class = None

    def __new__(cls, *args, **kwargs):
        if cls._real_class is None:
            cls._real_class = _get_deprecated_email_analysis_engine()
        return cls._real_class(*args, **kwargs)


class _DeprecatedEmailAnalyzer:
    """Wrapper that issues deprecation warning on instantiation."""

    _real_class = None

    def __new__(cls, *args, **kwargs):
        if cls._real_class is None:
            cls._real_class = _get_deprecated_email_analyzer()
        return cls._real_class(*args, **kwargs)


# Export deprecated classes with wrappers for backward compatibility
EmailAnalysisEngine = _DeprecatedEmailAnalysisEngine
EmailAnalyzer = _DeprecatedEmailAnalyzer


__all__ = [
    # Canonical implementation (recommended)
    'DailyEmailAnalyzer',
    'DataQualityAssessment',
    'HierarchicalClassifier',
    'TemporalAnalyzer',
    'SenderAnalyzer',
    'ContentAnalyzer',
    'InsightsGenerator',
    # Data converter
    'EmailDataConverter',
    # Legacy aliases (deprecated)
    'EmailAnalysisEngine',  # DEPRECATED: use DailyEmailAnalyzer
    'EmailAnalyzer',        # DEPRECATED: use DailyEmailAnalyzer
]
