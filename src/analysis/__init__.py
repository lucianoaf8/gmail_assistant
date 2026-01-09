"""
Email Analysis Module
====================

Sophisticated email classification and temporal pattern analysis.
"""

from .email_analyzer import EmailAnalysisEngine as EmailAnalyzer
from .daily_email_analysis import EmailAnalysisEngine
from .email_data_converter import EmailDataConverter

__all__ = [
    'EmailAnalyzer',
    'EmailAnalysisEngine',
    'EmailDataConverter'
]