"""
Output format plugins for Gmail Fetcher.

Available plugins:
- EmlOutputPlugin: Native EML format
- MarkdownOutputPlugin: Markdown format with metadata
- JsonOutputPlugin: JSON format for processing
"""

from .eml import EmlOutputPlugin
from .markdown import MarkdownOutputPlugin
from .json_output import JsonOutputPlugin

__all__ = [
    "EmlOutputPlugin",
    "MarkdownOutputPlugin",
    "JsonOutputPlugin",
]
