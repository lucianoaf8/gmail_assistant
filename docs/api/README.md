# API Documentation

Developer reference for Gman public APIs.

## Contents

| Document | Description |
|----------|-------------|
| [public-api-reference.md](public-api-reference.md) | Module and class APIs |
| [constants-reference.md](constants-reference.md) | System constants and enums |

## Quick Example

```python
from gman.core.fetch.gman import GmailFetcher
from gman.core.config import AppConfig

fetcher = GmailFetcher('credentials.json')
fetcher.authenticate()
emails = fetcher.fetch_emails(query="is:unread", max_results=100)
```
