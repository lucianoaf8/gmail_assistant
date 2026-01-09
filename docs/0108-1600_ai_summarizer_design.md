# AI Email Summarizer System Design

**Project**: Gmail Fetcher Suite
**Component**: AI-Powered Email Analysis and Summarization
**Date**: 2025-09-19
**Status**: Design Phase

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Email Summarizer                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Email Input   │  │  AI Processing  │  │ Report Output   │ │
│  │                 │  │                 │  │                 │ │
│  │ • EML files     │─▶│ • Individual    │─▶│ • Detailed      │ │
│  │ • Markdown      │  │   summaries     │  │   reports       │ │
│  │ • Database      │  │ • Batch         │  │ • Executive     │ │
│  │ • Live fetch    │  │   processing    │  │   summaries     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                │                               │
│  ┌─────────────────────────────▼─────────────────────────────┐ │
│  │              Multi-Provider API Layer                    │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │ │
│  │  │  Anthropic  │ │   OpenAI    │ │ TogetherAI  │ ...    │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Component Design

### 1. AI API Abstraction Layer (`src/ai/`)

**File: `src/ai/ai_provider_interface.py`**
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class SummaryRequest:
    content: str
    email_type: str  # newsletter, notification, marketing, personal
    metadata: Dict[str, Any]
    max_length: int = 200
    focus_areas: List[str] = None  # topics, actions, key_points

@dataclass
class SummaryResponse:
    summary: str
    key_points: List[str]
    sentiment: str
    confidence: float
    processing_time: float
    tokens_used: int

class AIProviderInterface(ABC):
    @abstractmethod
    async def summarize_email(self, request: SummaryRequest) -> SummaryResponse:
        pass

    @abstractmethod
    async def batch_summarize(self, requests: List[SummaryRequest]) -> List[SummaryResponse]:
        pass
```

**File: `src/ai/providers/`** - Individual provider implementations:
- `anthropic_provider.py` - Claude integration
- `openai_provider.py` - GPT models
- `together_provider.py` - TogetherAI models
- `openrouter_provider.py` - OpenRouter proxy

### 2. Email Content Processor (`src/ai/email_processor.py`)

```python
class EmailContentProcessor:
    def __init__(self, ai_provider: AIProviderInterface):
        self.ai_provider = ai_provider
        self.content_extractors = {
            'eml': EMLContentExtractor(),
            'markdown': MarkdownContentExtractor(),
            'html': HTMLContentExtractor()
        }

    async def process_single_email(self, email_path: str) -> EmailSummary:
        # Extract content, classify email type, prepare AI request

    async def process_batch(self, email_paths: List[str],
                          batch_size: int = 10) -> List[EmailSummary]:
        # Parallel processing with rate limiting
```

### 3. Summary Report Generator (`src/ai/report_generator.py`)

```python
class SummaryReportGenerator:
    def __init__(self, template_dir: str = "templates/"):
        self.templates = self._load_templates(template_dir)

    def generate_detailed_report(self, summaries: List[EmailSummary]) -> str:
        # Full email-by-email analysis with metadata

    def generate_executive_summary(self, summaries: List[EmailSummary]) -> str:
        # High-level insights, trends, key information

    def generate_category_analysis(self, summaries: List[EmailSummary]) -> Dict:
        # Group by sender, type, sentiment, urgency
```

## Integration Points with Existing System

### 1. Command Line Integration
Extend `main.py` with new `summarize` command:

```python
# Add to main.py subparsers
summarize_parser = subparsers.add_parser('summarize', help='AI-powered email analysis')
summarize_parser.add_argument('--input', required=True, help='Email source (folder/database)')
summarize_parser.add_argument('--provider', choices=['anthropic', 'openai', 'together', 'openrouter'],
                             default='anthropic')
summarize_parser.add_argument('--output-format', choices=['json', 'markdown', 'html'],
                             default='markdown')
summarize_parser.add_argument('--batch-size', type=int, default=10)
summarize_parser.add_argument('--report-type', choices=['detailed', 'executive', 'category'],
                             default='executive')
```

### 2. Database Integration
Extend existing database schema to store summaries:

```sql
-- Add to existing email database
ALTER TABLE emails ADD COLUMN ai_summary TEXT;
ALTER TABLE emails ADD COLUMN key_points JSON;
ALTER TABLE emails ADD COLUMN sentiment VARCHAR(20);
ALTER TABLE emails ADD COLUMN summary_confidence REAL;
ALTER TABLE emails ADD COLUMN processed_date TIMESTAMP;

-- New summary reports table
CREATE TABLE summary_reports (
    id INTEGER PRIMARY KEY,
    report_type VARCHAR(50),
    date_range TEXT,
    total_emails INTEGER,
    report_content TEXT,
    generated_date TIMESTAMP
);
```

### 3. Configuration Design

**File: `config/ai_summarizer_config.json`**
```json
{
    "providers": {
        "anthropic": {
            "api_key_env": "ANTHROPIC_API_KEY",
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "temperature": 0.1,
            "rate_limit": 5
        },
        "openai": {
            "api_key_env": "OPENAI_API_KEY",
            "model": "gpt-4-turbo-preview",
            "max_tokens": 4000,
            "temperature": 0.1,
            "rate_limit": 10
        },
        "together": {
            "api_key_env": "TOGETHER_API_KEY",
            "model": "meta-llama/Llama-3-70b-chat-hf",
            "max_tokens": 4000,
            "rate_limit": 8
        }
    },
    "processing": {
        "batch_size": 10,
        "max_content_length": 16000,
        "retry_attempts": 3,
        "timeout_seconds": 30
    },
    "summary_settings": {
        "default_max_length": 200,
        "include_sentiment": true,
        "extract_key_points": true,
        "focus_areas": ["actions_required", "key_information", "deadlines"]
    },
    "report_templates": {
        "executive": "templates/executive_summary.md",
        "detailed": "templates/detailed_report.md",
        "category": "templates/category_analysis.md"
    }
}
```

## Recommended Implementation Strategy

### Phase 1: Core Infrastructure (Week 1)
1. **AI Provider Abstraction Layer**: Create base interfaces and provider implementations
2. **Configuration System**: Setup config files and environment variable management
3. **Basic Email Processing**: Single email summarization with one provider (Anthropic)

### Phase 2: Processing & Integration (Week 2)
1. **Batch Processing**: Implement concurrent email processing with rate limiting
2. **Database Integration**: Extend schema and add persistence for summaries
3. **Command Line Interface**: Add `summarize` command to main.py

### Phase 3: Reports & Enhancement (Week 3)
1. **Report Generation**: Implement all report types with templates
2. **Multi-Provider Support**: Add remaining AI providers (OpenAI, Together, OpenRouter)
3. **Advanced Features**: Filtering, classification-aware summaries, export options

## Usage Examples

```bash
# Basic email summarization
python main.py summarize --input backup_unread/ --provider anthropic

# Executive summary report
python main.py summarize --input backups/2024/ --report-type executive --output-format html

# Category analysis with specific provider
python main.py summarize --input data/emails.db --provider openai --report-type category

# Batch processing with custom settings
python main.py summarize --input backups/ --batch-size 5 --provider together
```

## Cost and Performance Considerations

### API Cost Management
- **Token estimation**: Pre-calculate costs based on content length
- **Provider comparison**: Route requests to most cost-effective provider
- **Caching**: Store processed summaries to avoid re-processing
- **Batch optimization**: Group similar emails for efficiency

### Performance Optimization
- **Concurrent processing**: Parallel API calls within rate limits
- **Content preprocessing**: Smart truncation and cleaning
- **Provider fallback**: Switch providers on failures
- **Progress tracking**: Real-time processing status

## File Structure

```
src/ai/
├── __init__.py
├── ai_provider_interface.py      # Abstract base classes
├── email_processor.py            # Core processing logic
├── report_generator.py           # Report generation
├── content_extractors.py         # Email content extraction
├── providers/
│   ├── __init__.py
│   ├── anthropic_provider.py     # Claude integration
│   ├── openai_provider.py        # GPT models
│   ├── together_provider.py      # TogetherAI
│   └── openrouter_provider.py    # OpenRouter proxy
└── utils/
    ├── __init__.py
    ├── rate_limiter.py           # API rate limiting
    ├── token_calculator.py       # Cost estimation
    └── caching.py                # Summary caching

config/
└── ai_summarizer_config.json    # AI configuration

templates/
├── executive_summary.md         # Executive report template
├── detailed_report.md           # Detailed analysis template
└── category_analysis.md         # Category breakdown template
```

## Dependencies

### New Requirements
```txt
# AI Providers
anthropic>=0.15.0
openai>=1.10.0
together>=0.2.0

# Async and concurrency
aiohttp>=3.8.0
asyncio-throttle>=1.0.0

# Template processing
jinja2>=3.1.0

# Configuration
pydantic>=2.0.0

# Progress tracking
tqdm>=4.64.0
```

## Security Considerations

### API Key Management
- Store API keys in environment variables only
- Never commit API keys to version control
- Implement key rotation support
- Add validation for API key format

### Data Privacy
- Sanitize email content before sending to AI providers
- Option to exclude sensitive content patterns
- Local processing mode for highly sensitive emails
- Clear data retention policies for AI provider logs

## Testing Strategy

### Unit Tests
- Mock AI provider responses for consistent testing
- Test rate limiting and error handling
- Validate summary quality metrics
- Configuration validation tests

### Integration Tests
- End-to-end email processing workflows
- Database integration with summary storage
- Report generation with real data
- Multi-provider fallback scenarios

### Performance Tests
- Batch processing with large email volumes
- Memory usage monitoring during processing
- API response time measurements
- Concurrent processing stress tests

## Future Enhancements

### Advanced Features
- **Smart filtering**: Skip already-summarized emails
- **Content classification**: Automatic email type detection
- **Trend analysis**: Identify patterns across time periods
- **Action extraction**: Identify actionable items and deadlines

### UI Integration
- **Web dashboard**: Browser-based report viewing
- **Interactive reports**: Drill-down capabilities
- **Real-time processing**: Live summary generation
- **Export options**: PDF, Excel, CSV report formats

### AI Improvements
- **Model fine-tuning**: Custom models for email-specific tasks
- **Multi-language support**: International email processing
- **Sentiment tracking**: Emotional analysis over time
- **Entity extraction**: People, companies, topics identification

---

**Design Status**: ✅ Complete
**Next Phase**: Implementation - Phase 1 (Core Infrastructure)
**Estimated Timeline**: 3 weeks for full implementation
**Priority**: High - Adds significant value to existing email analysis capabilities