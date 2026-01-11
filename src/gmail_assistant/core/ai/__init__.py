"""AI sub-package for AI-powered email processing."""

from .newsletter_cleaner import AINewsletterCleaner, AINewsletterDetector, GmailCleaner


# Lazy import for GmailAnalysisIntegration to avoid requiring pyarrow at import time
def __getattr__(name):
    """Lazy import handler for optional dependencies."""
    if name == 'GmailAnalysisIntegration':
        from .analysis_integration import GmailAnalysisIntegration
        return GmailAnalysisIntegration
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    'AINewsletterCleaner',
    'AINewsletterDetector',
    'GmailAnalysisIntegration',
    'GmailCleaner',
]
