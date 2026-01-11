"""Processing sub-package for email content processing."""

from .classifier import EmailClassifier
from .database import EmailDatabaseImporter
from .extractor import EmailDataExtractor
from .plaintext import EmailPlaintextProcessor

__all__ = [
    'EmailClassifier',
    'EmailDataExtractor',
    'EmailDatabaseImporter',
    'EmailPlaintextProcessor',
]
