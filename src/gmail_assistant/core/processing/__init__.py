"""Processing sub-package for email content processing."""

from .classifier import EmailClassifier
from .extractor import EmailDataExtractor
from .plaintext import EmailPlaintextProcessor
from .database import EmailDatabaseImporter

__all__ = [
    'EmailClassifier',
    'EmailDataExtractor',
    'EmailPlaintextProcessor',
    'EmailDatabaseImporter',
]
