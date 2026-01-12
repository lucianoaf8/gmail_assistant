"""Processing sub-package for email content processing."""

from .classifier import EmailClassifier
from .database import EmailDatabaseImporter
from .extractor import EmailDataExtractor
from .file_repository import FileEmailRepository
from .plaintext import EmailPlaintextProcessor

__all__ = [
    'EmailClassifier',
    'EmailDataExtractor',
    'EmailDatabaseImporter',
    'EmailPlaintextProcessor',
    'FileEmailRepository',
]
