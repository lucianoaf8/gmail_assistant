"""AI sub-package for AI-powered email processing."""

from .newsletter_cleaner import AINewsletterCleaner
from .analysis_integration import GmailAnalysisIntegration

__all__ = [
    'AINewsletterCleaner',
    'GmailAnalysisIntegration',
]
