"""
Shared pagination utilities for Gmail API operations.

M-15: Extracted to provide consistent pagination across all fetchers.

Usage:
    from gmail_assistant.utils.pagination import Paginator, PaginationConfig

    config = PaginationConfig(max_results=1000, page_size=100)
    paginator = Paginator(config)

    for page in paginator.paginate(fetch_page_func):
        process(page)
"""
from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass(frozen=True)
class PaginationConfig:
    """Configuration for pagination behavior.

    Attributes:
        max_results: Maximum total items to fetch (0 = unlimited)
        page_size: Items per page (Gmail API max is 500)
        max_pages: Maximum pages to fetch (0 = unlimited)
    """
    max_results: int = 1000
    page_size: int = 100
    max_pages: int = 0  # 0 = unlimited

    def __post_init__(self) -> None:
        if self.page_size < 1 or self.page_size > 500:
            raise ValueError("page_size must be 1-500 (Gmail API limit)")
        if self.max_results < 0:
            raise ValueError("max_results must be >= 0")


@dataclass
class PageResult(Generic[T]):
    """Result from a single page fetch.

    Attributes:
        items: Items from this page
        next_page_token: Token for next page (None if last page)
        page_number: Current page number (1-based)
        total_fetched: Total items fetched so far
    """
    items: list[T]
    next_page_token: str | None
    page_number: int
    total_fetched: int


class Paginator(Generic[T]):
    """Reusable pagination handler for Gmail API.

    M-15: Centralizes pagination logic to avoid code duplication.

    Example:
        def fetch_page(page_token: str | None, page_size: int) -> tuple[list, str | None]:
            result = service.users().messages().list(
                userId='me', maxResults=page_size, pageToken=page_token
            ).execute()
            return result.get('messages', []), result.get('nextPageToken')

        paginator = Paginator(PaginationConfig(max_results=500))
        for page in paginator.paginate(fetch_page):
            for item in page.items:
                process(item)
    """

    def __init__(self, config: PaginationConfig | None = None):
        """Initialize paginator with optional config."""
        self.config = config or PaginationConfig()
        self._total_fetched = 0
        self._page_count = 0

    def reset(self) -> None:
        """Reset pagination state for reuse."""
        self._total_fetched = 0
        self._page_count = 0

    def paginate(
        self,
        fetch_func: Callable[[str | None, int], tuple[list[T], str | None]],
    ) -> Iterator[PageResult[T]]:
        """
        Paginate through results using the provided fetch function.

        Args:
            fetch_func: Function that takes (page_token, page_size) and returns
                       (items, next_page_token)

        Yields:
            PageResult for each page
        """
        self.reset()
        page_token: str | None = None

        while True:
            # Check page limit
            if self.config.max_pages > 0 and self._page_count >= self.config.max_pages:
                logger.debug(f"Reached max_pages limit: {self.config.max_pages}")
                break

            # Calculate page size for this request
            remaining = self.config.max_results - self._total_fetched
            if self.config.max_results > 0 and remaining <= 0:
                break

            page_size = min(self.config.page_size, remaining) if self.config.max_results > 0 else self.config.page_size

            # Fetch page
            try:
                items, next_token = fetch_func(page_token, page_size)
            except Exception as e:
                logger.error(f"Pagination fetch failed on page {self._page_count + 1}: {e}")
                raise

            self._page_count += 1
            self._total_fetched += len(items)

            yield PageResult(
                items=items,
                next_page_token=next_token,
                page_number=self._page_count,
                total_fetched=self._total_fetched,
            )

            # Check if more pages available
            page_token = next_token
            if not page_token:
                break

            # Check if we've hit max_results
            if self.config.max_results > 0 and self._total_fetched >= self.config.max_results:
                logger.debug(f"Reached max_results limit: {self.config.max_results}")
                break

        logger.info(
            f"Pagination complete: {self._total_fetched} items across {self._page_count} pages"
        )

    @property
    def total_fetched(self) -> int:
        """Total items fetched across all pages."""
        return self._total_fetched

    @property
    def page_count(self) -> int:
        """Number of pages fetched."""
        return self._page_count


def paginate_all(
    fetch_func: Callable[[str | None, int], tuple[list[T], str | None]],
    max_results: int = 1000,
    page_size: int = 100,
) -> list[T]:
    """
    Convenience function to fetch all items across pages.

    Args:
        fetch_func: Function that takes (page_token, page_size) and returns
                   (items, next_page_token)
        max_results: Maximum items to fetch
        page_size: Items per page

    Returns:
        All items as a single list
    """
    config = PaginationConfig(max_results=max_results, page_size=page_size)
    paginator: Paginator[T] = Paginator(config)
    all_items: list[T] = []

    for page in paginator.paginate(fetch_func):
        all_items.extend(page.items)

    return all_items


def paginate_streaming(
    fetch_func: Callable[[str | None, int], tuple[list[T], str | None]],
    max_results: int = 1000,
    page_size: int = 100,
) -> Iterator[T]:
    """
    Convenience generator to stream items one at a time.

    Args:
        fetch_func: Function that takes (page_token, page_size) and returns
                   (items, next_page_token)
        max_results: Maximum items to fetch
        page_size: Items per page

    Yields:
        Individual items
    """
    config = PaginationConfig(max_results=max_results, page_size=page_size)
    paginator: Paginator[T] = Paginator(config)

    for page in paginator.paginate(fetch_func):
        yield from page.items
