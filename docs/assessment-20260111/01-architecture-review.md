# Architecture Review: Gmail Assistant v2.0.0

**Review Date**: 2026-01-11
**Reviewer**: Software Architecture Specialist
**Codebase Version**: v2.0.0 (commit 418db43)

---

## Executive Summary

The gmail-assistant project demonstrates a **well-structured, protocol-driven architecture** with strong foundations in dependency injection, clean separation of concerns, and comprehensive error handling. The v2.0.0 refactoring successfully implemented src-layout packaging and Click-based CLI.

**Overall Architecture Grade**: B+ (Good with notable areas for improvement)

### Key Strengths
1. **Excellent protocol-based design** - 17 well-defined protocols in `core/protocols.py` enable structural subtyping and testability
2. **Strong dependency injection** - Lightweight DI container with singleton/transient/scoped lifetimes
3. **Comprehensive exception hierarchy** - Centralized in `core/exceptions.py` with clear domain boundaries
4. **Modern async patterns** - AsyncGmailFetcher with proper semaphore control and thread pool management
5. **Security-first configuration** - Credentials default to `~/.gmail-assistant/` (outside repositories)

### Critical Issues (3)
| Severity | Count | Primary Concern |
|----------|-------|-----------------|
| CRITICAL | 3 | Duplicate rate limiters, missing repository implementation, circular import risk |
| HIGH | 8 | Module coupling, inconsistent patterns, scalability bottlenecks |
| MEDIUM | 12 | Design pattern inconsistencies, documentation gaps |
| LOW | 6 | Optimization opportunities, minor architectural debt |

### Immediate Action Items
1. **Consolidate rate limiters** - Resolve `utils/rate_limiter.py` vs `core/auth/rate_limiter.py` duplication
2. **Implement EmailRepository** - Protocol exists but no file-based implementation (M-9 incomplete)
3. **Break circular import risk** - `core/__init__.py` lazy imports create fragile dependency graph

---

## Detailed Findings

### 1. Module Boundaries and Coupling

#### Architecture Overview
```
src/gmail_assistant/
├── cli/                    # Click-based CLI (420 LOC main.py)
│   └── commands/          # Command implementations (135-254 LOC each)
├── core/                  # Domain logic (8 subpackages)
│   ├── auth/             # Authentication (3 classes)
│   ├── fetch/            # Email fetching (8 implementations)
│   ├── processing/       # Content processing (4 processors)
│   ├── ai/               # AI features (2 modules)
│   └── output/           # Plugin system (1 manager)
├── analysis/             # Email analysis (5 analyzers, largest: 1321 LOC)
├── deletion/             # Email deletion (3 modules)
├── export/               # Data export (1 Parquet exporter)
├── parsers/              # Email parsing (3 parsers)
└── utils/                # Shared utilities (12 modules)
```

#### Findings Table

| Issue | Severity | Location | Description |
|-------|----------|----------|-------------|
| Duplicate RateLimiter classes | CRITICAL | `utils/rate_limiter.py` vs `core/auth/rate_limiter.py` | Two independent rate limiters: `GmailRateLimiter` (API) and `AuthRateLimiter` (auth). Naming collision creates confusion. `GmailRateLimiter` is used by 3 modules, `AuthRateLimiter` unused. |
| Missing EmailRepository implementation | CRITICAL | `core/protocols.py` (L641-723) | `EmailRepositoryProtocol` defined but no file-based implementation exists. Only `EmailDatabaseImporter` (SQLite) registered in container. M-9 fix incomplete. |
| Lazy import fragility | CRITICAL | `core/__init__.py` (L33-102) | `__getattr__` with 25+ lazy imports creates runtime import errors. Fails fast only on first access, not import time. Breaks static analysis tools. |
| Tight coupling: CLI → Core | HIGH | `cli/commands/*.py` | CLI commands directly instantiate core classes (`GmailFetcher`, `GmailAPIClient`) instead of using DI container. Violates dependency inversion. |
| God object: GmailFetcher | HIGH | `core/fetch/gmail_assistant.py` (551 LOC) | Violates SRP: authentication, API calls, file I/O, parsing, organization all in one class. Should delegate to plugins. |
| Circular dependency risk | HIGH | `core/container.py` imports `core/processing/database.py` | Container imports concrete implementation for factory function. Breaks DI abstraction boundary. |
| analysis/ module isolation | MEDIUM | `analysis/` (5 modules) | No `analysis/` imports in core, but core exports analysis classes. Suggests incomplete modularization. |
| utils/ as catch-all | MEDIUM | `utils/` (12 disparate modules) | Contains unrelated utilities: cache, memory, metrics, validators, loggers. Should split into domain-specific modules. |
| Export module underutilized | LOW | `export/` (1 Parquet exporter) | Only 1 exporter. Consider merging into `core/output/` plugin system or expanding export capabilities. |

**Architecture Impact**: HIGH - Duplicate rate limiters and missing repository create confusion and technical debt.

---

### 2. Dependency Structure

#### Internal Dependency Analysis

**Most-Imported Modules** (by other modules):
1. `core/exceptions.py` - 11 imports (excellent centralization)
2. `utils/secure_logger.py` - 7 imports
3. `core/config.py` - 4 imports
4. `utils/input_validator.py` - 4 imports
5. `core/schemas.py` - 3 imports

**Dependency Injection Coverage**:
- **Registered in container**: `CacheManager`, `GmailRateLimiter`, `InputValidator`, `ErrorHandler`, `EmailRepositoryProtocol`
- **Not using DI**: CLI commands, parsers, analysis modules (direct instantiation)

#### Findings Table

| Issue | Severity | Location | Description |
|-------|----------|----------|-------------|
| No circular imports detected | INFO | Project-wide | Clean import graph. Excellent architectural discipline. |
| Container factory imports concrete class | HIGH | `core/container.py` (L348) | `create_default_container()` imports `EmailDatabaseImporter` directly. Should register interface, not implementation. |
| CLI bypasses DI container | HIGH | `cli/commands/*.py` | Commands instantiate `GmailFetcher(credentials_file)` directly instead of resolving from container. Limits testability and flexibility. |
| Redundant protocol checks | MEDIUM | `core/protocols.py` (L894-924) | `implements_protocol()` and `assert_protocol()` utilities exist but unused in codebase. Dead code or missing enforcement? |
| Missing protocol implementations | MEDIUM | `core/protocols.py` | 17 protocols defined, but no `@runtime_checkable` validation in consuming code. Protocols are documentation-only. |
| Inconsistent import patterns | LOW | Project-wide | Mix of absolute (`gmail_assistant.core.X`) and relative (`from .X import`) imports. Standardize on absolute imports. |

**Architecture Impact**: MEDIUM - DI container underutilized, but dependency graph is clean.

---

### 3. Design Pattern Consistency

#### Pattern Inventory

| Pattern | Implementation | Usage | Quality |
|---------|---------------|-------|---------|
| **Repository** | `EmailRepositoryProtocol` (L641) | Protocol defined, SQLite impl only | INCOMPLETE - No file-based impl |
| **Strategy** | `OutputPlugin` (plugin_manager.py) | EML, Markdown plugins | GOOD - Clean abstraction |
| **Dependency Injection** | `ServiceContainer` (container.py) | 5 registered services | UNDERUTILIZED - CLI bypasses |
| **Protocol/Interface** | 17 protocols in `protocols.py` | Structural typing | EXCELLENT - Comprehensive |
| **Factory** | Container factory functions (L327+) | 4 factory methods | GOOD - Clear separation |
| **Singleton** | ServiceLifetime.SINGLETON | CacheManager, RateLimiter | GOOD - Thread-safe |
| **Async/Await** | `AsyncGmailFetcher` | Concurrent operations | GOOD - Proper semaphore use |
| **Circuit Breaker** | `utils/circuit_breaker.py` | Error resilience | EXISTS - Usage unclear |

#### Findings Table

| Issue | Severity | Location | Description |
|-------|----------|----------|-------------|
| Repository pattern incomplete | CRITICAL | `core/protocols.py` + `core/processing/` | `EmailRepositoryProtocol` exists, but only SQLite implementation (`EmailDatabaseImporter`). M-9 fix promises file-based storage but missing. |
| Inconsistent plugin architecture | HIGH | `core/output/` vs parsers | `OutputPlugin` uses ABC pattern, but parsers (`advanced_email_parser.py`) use strategy pattern without base class. Inconsistent abstractions. |
| Two exception strategies | HIGH | `core/exceptions.py` vs `core/auth/base.py` | `AuthenticationError` defined in both `exceptions.py` and `auth/base.py`. Violates single source of truth. |
| Deprecated classes in production | HIGH | `core/protocols.py` (L36-60), `core/schemas.py` (L254-327) | `EmailMetadata`, `EmailMetadataCompat`, `EmailDataCompat` marked deprecated but still in use. Should remove or migrate fully. |
| Protocol enforcement missing | MEDIUM | All protocol consumers | Protocols defined with `@runtime_checkable` but no `isinstance()` checks in consuming code. Static typing only. |
| Mixed ABC and Protocol usage | MEDIUM | `core/output/plugin_manager.py` vs `core/protocols.py` | `OutputPlugin` uses `ABC`, protocols use `Protocol`. Should standardize on one approach. |
| Circuit breaker underused | LOW | `utils/circuit_breaker.py` | Exists but no imports found in codebase. Dead code or future feature? |

**Architecture Impact**: HIGH - Repository incomplete, inconsistent patterns reduce maintainability.

---

### 4. Scalability Concerns

#### Performance Architecture

**Async Implementation**:
- `AsyncGmailFetcher` (async_fetcher.py): Semaphore-controlled concurrency, ThreadPoolExecutor for blocking I/O
- `StreamingGmailFetcher` (streaming.py): Generator-based lazy loading
- Max concurrent operations: 10 (configurable)
- Thread pool workers: 4 (configurable)

**Batch Processing**:
- `BatchAPI` (batch_api.py): Gmail batch API support (up to 100 requests/batch)
- `IncrementalFetcher` (incremental.py): History API for delta syncs
- Checkpoint system (checkpoint.py): Resume interrupted operations

**Memory Management**:
- `MemoryTracker`: 500MB warning, 1GB critical thresholds
- `StreamingEmailProcessor`: Chunk-based processing (100 emails/chunk)
- Explicit garbage collection triggers

#### Findings Table

| Issue | Severity | Location | Description |
|-------|----------|----------|-------------|
| Sync-over-async anti-pattern | HIGH | `core/fetch/async_fetcher.py` (L57-69) | `_sync_api_call` wraps synchronous Gmail API in async executor. True async client would be better (httpx/aiohttp). Thread pool overhead adds latency. |
| Hardcoded concurrency limits | MEDIUM | `AsyncGmailFetcher.__init__` | `max_concurrent=10`, `max_workers=4` hardcoded. Should be configurable via AppConfig for different machine sizes. |
| No backpressure mechanism | MEDIUM | `streaming.py` | `StreamingGmailFetcher` yields indefinitely without consumer feedback. Risk of overwhelming downstream processors. |
| Memory thresholds arbitrary | MEDIUM | `utils/memory_manager.py` (L24-25) | 500MB/1GB thresholds fixed. Should be percentage of available RAM (e.g., 50%/80%). Breaks on low-memory systems. |
| Single-threaded batch API | MEDIUM | `core/fetch/batch_api.py` | Batch requests processed sequentially. Could parallelize batch preparation and response parsing. |
| No connection pooling | LOW | Gmail API client usage | Each operation creates new HTTP connection. Should use persistent session with connection pooling. |
| Dead letter queue incomplete | LOW | `core/fetch/dead_letter_queue.py` (513 LOC) | Sophisticated DLQ implementation but no retry orchestration in main flow. |

**Architecture Impact**: MEDIUM - Async implementation works but suboptimal for high-throughput scenarios.

---

### 5. Configuration Architecture

#### Configuration System Design

**Resolution Order** (config.py):
1. CLI arguments (`--config`)
2. Environment variable (`gmail_assistant_CONFIG`)
3. Project config (`./gmail-assistant.json`)
4. User config (`~/.gmail-assistant/config.json`)
5. Built-in defaults

**Schema Validation**:
- `AppConfig` dataclass with `__post_init__` validation
- Frozen/immutable after creation
- Strict allowed keys (`_ALLOWED_KEYS` frozenset)
- Type validation on load

**Security Features**:
- Credentials default to `~/.gmail-assistant/` (outside repos)
- Repo-local credentials require `--allow-repo-credentials` flag
- Path expansion and validation (`~`, relative paths)

#### Findings Table

| Issue | Severity | Location | Description |
|-------|----------|----------|-------------|
| Plugin system not integrated with config | HIGH | `core/output/plugin_manager.py` vs `core/config.py` | OutputPlugin selection hardcoded in `GmailFetcher`. Should be configurable in AppConfig (e.g., `output_plugins: ["eml", "markdown"]`). |
| Config schema split across files | MEDIUM | `core/config.py`, `core/config_schemas.py`, `utils/config_schema.py` | Three separate config-related modules. Consolidate into single source. |
| No config migration path | MEDIUM | `core/config.py` | Schema changes will break existing configs. Need versioning and migration strategy. |
| Hard-coded paths | MEDIUM | Throughout codebase | Paths like `AI_CONFIG_PATH`, `KEYRING_SERVICE` in `core/constants.py`. Should be configurable. |
| Rate limits not configurable | LOW | `utils/rate_limiter.py` | `requests_per_second=10.0` in code. Should come from AppConfig. |
| No environment-specific configs | LOW | N/A | No support for dev/staging/prod configurations. Single global config only. |

**Architecture Impact**: MEDIUM - Config system is solid but plugin architecture disconnected.

---

## Recommendations

### Priority 1: Critical Fixes (Immediate)

#### 1.1 Consolidate Rate Limiters
**Problem**: Two rate limiters with overlapping purpose create confusion.

**Solution**:
```python
# Keep: utils/rate_limiter.py -> GmailRateLimiter (API rate limiting)
# Rename: core/auth/rate_limiter.py -> AuthenticationThrottler (auth brute-force protection)
# Clarify: Different purposes, different names
```

**Impact**: Eliminates architectural ambiguity, clarifies intent.

#### 1.2 Implement File-Based EmailRepository
**Problem**: M-9 fix incomplete - protocol exists but no file implementation.

**Solution**:
```python
# New: core/processing/file_repository.py
class FileEmailRepository(EmailRepositoryProtocol):
    """File-based email storage using JSON/EML files."""
    def save(self, email: dict) -> bool: ...
    def get(self, email_id: str) -> dict | None: ...
    # ... implement protocol methods
```

**Impact**: Completes M-9 fix, enables storage flexibility.

#### 1.3 Replace Lazy Imports with Explicit Exports
**Problem**: `core/__init__.py` `__getattr__` creates runtime failures.

**Solution**:
```python
# Replace __getattr__ with conditional imports:
try:
    from .fetch.gmail_assistant import GmailFetcher
except ImportError:
    GmailFetcher = None  # type: ignore

__all__ = [...]  # Explicit list
```

**Impact**: Fail-fast at import time, better IDE support.

---

### Priority 2: High-Impact Improvements (1-2 weeks)

#### 2.1 Refactor GmailFetcher (God Object → Composition)
**Current**: 551 LOC, 10+ responsibilities
**Target**: 200 LOC coordinator, delegate to:
- `EmailSearcher` (search/pagination)
- `EmailDownloader` (API calls)
- `EmailWriter` (file I/O via OutputPlugin)
- `EmailOrganizer` (date/sender organization)

**Impact**: Testability ↑, maintainability ↑, SRP compliance.

#### 2.2 Integrate DI Container with CLI
**Current**: CLI commands instantiate core classes directly
**Target**:
```python
# cli/commands/fetch.py
@click.command()
@click.pass_context
def fetch_emails(ctx):
    container = ctx.obj['container']
    fetcher = container.resolve(GmailFetcher)
    fetcher.download_emails(...)
```

**Impact**: Testability ↑, configuration flexibility ↑.

#### 2.3 Make Configuration Hierarchical
**Current**: Flat AppConfig with 6 fields
**Target**:
```python
@dataclass
class AppConfig:
    auth: AuthConfig      # credentials_path, token_path
    fetch: FetchConfig    # max_emails, rate_limit
    output: OutputConfig  # plugins, organize_by, formats
    logging: LogConfig    # log_level, log_file
```

**Impact**: Scalability ↑, clarity ↑, future extensibility.

---

### Priority 3: Medium-Term Enhancements (1 month)

#### 3.1 Implement True Async Client
Replace sync-over-async pattern with native async:
```python
# Use httpx or aiohttp for Gmail API calls
# Eliminate ThreadPoolExecutor overhead
# 2-3x throughput improvement expected
```

#### 3.2 Add Protocol Runtime Validation
Enforce protocols at critical boundaries:
```python
from core.protocols import assert_protocol, EmailFetcherProtocol

def register_fetcher(fetcher):
    assert_protocol(fetcher, EmailFetcherProtocol, "fetcher")
    # ... use fetcher
```

#### 3.3 Consolidate Config Modules
Merge `config.py`, `config_schemas.py`, `utils/config_schema.py` into single `core/config/` package.

---

### Priority 4: Long-Term Strategic (3+ months)

#### 4.1 Plugin Architecture Expansion
Unify output plugins, parsers, analyzers under single plugin system:
```python
class PluginRegistry:
    def register(self, plugin_type: str, plugin: Plugin): ...
    def get(self, plugin_type: str, name: str) -> Plugin: ...

# Usage:
registry.register("output", EMLPlugin())
registry.register("parser", AdvancedEmailParser())
registry.register("analyzer", EmailClassifier())
```

#### 4.2 Event-Driven Architecture
Introduce event bus for cross-module communication:
```python
# Decouple modules via events instead of direct imports
events.emit("email.downloaded", email_data)
# analysis/ module subscribes without core/ dependency
```

#### 4.3 Microservices Preparation
Current monolith is ready for decomposition:
- **Auth Service**: `core/auth/` → standalone OAuth service
- **Fetch Service**: `core/fetch/` → email retrieval API
- **Processing Service**: `core/processing/` + `parsers/` → content extraction
- **Analysis Service**: `analysis/` → analytics and insights

**Trade-off**: Increased operational complexity vs. independent scalability.

---

## Quality Attribute Assessment

### Reliability: B+ (Good)
- ✅ Comprehensive exception hierarchy
- ✅ Dead letter queue for failed operations
- ✅ Checkpoint/resume capability
- ⚠️ Limited circuit breaker usage
- ❌ No global retry orchestration

### Scalability: B (Acceptable)
- ✅ Async/await implementation
- ✅ Streaming and batch processing
- ✅ Memory tracking and optimization
- ⚠️ Sync-over-async limits throughput
- ❌ No horizontal scaling support (single-process)

### Maintainability: B+ (Good)
- ✅ Clean module boundaries
- ✅ Protocol-driven design
- ✅ Dependency injection foundation
- ⚠️ Some god objects (GmailFetcher, daily_email_analyzer)
- ❌ Inconsistent plugin patterns

### Security: A- (Excellent)
- ✅ Credentials outside repositories by default
- ✅ Secure credential manager with keyring
- ✅ Auth rate limiting (brute-force protection)
- ✅ PII redaction utilities
- ⚠️ No secrets scanning in CI/CD

### Testability: B (Acceptable)
- ✅ Protocols enable mocking
- ✅ DI container supports test doubles
- ⚠️ CLI not using DI (hard to test)
- ❌ Test coverage config excludes most code (see pyproject.toml L140-161)

### Performance: B (Acceptable)
- ✅ Batch API support (100 req/batch)
- ✅ Incremental sync with history API
- ✅ Memory-efficient streaming
- ⚠️ Sync-over-async overhead
- ❌ No connection pooling

---

## Architecture Diagrams

### Current Dependency Graph
```
┌─────────────────────────────────────────────────────────┐
│                      CLI Layer                          │
│  cli/main.py → cli/commands/* → Direct instantiation    │
└────────────────────┬────────────────────────────────────┘
                     │ (Should use DI)
                     ↓
┌─────────────────────────────────────────────────────────┐
│                    Core Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐           │
│  │   auth   │  │  fetch   │  │ processing │           │
│  │  (3 cls) │→ │ (8 impl) │→ │  (4 proc)  │           │
│  └──────────┘  └──────────┘  └────────────┘           │
│        ↑            ↑               ↑                   │
│        └────────────┴───────────────┴───────┐          │
│                                              ↓          │
│  ┌──────────────────────────────────────────────────┐  │
│  │          protocols.py (17 protocols)            │  │
│  │       exceptions.py (10 domain exceptions)      │  │
│  │         container.py (DI container)             │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  Utility Layer                          │
│  rate_limiter, memory_manager, cache_manager, etc.      │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│               External Dependencies                      │
│  google-api-python-client, click, pandas, etc.          │
└─────────────────────────────────────────────────────────┘
```

### Recommended Architecture (Future State)
```
┌─────────────────────────────────────────────────────────┐
│                      CLI Layer                          │
│      cli/main.py → Resolve from DI Container            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                 Service Container                        │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐      │
│  │AuthService │  │FetchService│  │OutputService │      │
│  └────────────┘  └────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                   Plugin Registry                        │
│  Output • Parser • Analyzer • Exporter plugins          │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│                   Event Bus (Future)                     │
│  email.fetched • email.parsed • email.analyzed          │
└─────────────────────────────────────────────────────────┘
```

---

## Compliance with Architectural Principles

### SOLID Principles
| Principle | Grade | Evidence |
|-----------|-------|----------|
| Single Responsibility | B | ✅ Most classes focused, ❌ GmailFetcher violates |
| Open/Closed | A- | ✅ OutputPlugin extensible, ✅ Protocol-based |
| Liskov Substitution | A | ✅ Protocols ensure substitutability |
| Interface Segregation | B+ | ✅ Fine-grained protocols, ⚠️ Some fat interfaces |
| Dependency Inversion | B | ✅ Protocols abstract deps, ❌ CLI violates |

### Clean Architecture
- ✅ **Entities**: Email, AppConfig (core domain models)
- ✅ **Use Cases**: Fetch, Delete, Analyze (application logic)
- ✅ **Interface Adapters**: CLI, OutputPlugins (presentation/persistence)
- ⚠️ **Frameworks**: Gmail API abstracted but coupled in places

### Domain-Driven Design
- ✅ **Bounded Contexts**: Auth, Fetch, Processing clearly separated
- ✅ **Ubiquitous Language**: Email, Message, Thread terminology consistent
- ❌ **Aggregates**: No aggregate root pattern (emails treated as flat entities)
- ❌ **Domain Events**: No event-driven communication

---

## Conclusion

The gmail-assistant v2.0.0 architecture demonstrates **mature software engineering practices** with protocol-driven design, dependency injection, and comprehensive error handling. The project is well-positioned for growth with a few critical fixes needed.

### Top 3 Actions for Maximum Impact
1. **Consolidate rate limiters** → Clear architectural intent
2. **Implement FileEmailRepository** → Complete M-9 fix
3. **Refactor GmailFetcher** → Eliminate god object, improve testability

### Strategic Direction
The current monolithic architecture is appropriate for the project's scale. Future growth should consider:
- **Near-term (6 months)**: Plugin architecture expansion, DI integration with CLI
- **Medium-term (12 months)**: Event-driven decoupling, true async client
- **Long-term (18+ months)**: Evaluate microservices if scaling requirements emerge

**Final Assessment**: Strong architectural foundation with tactical debt that can be resolved incrementally without major rewrites.

---

## Appendix: Architecture Metrics

### Codebase Statistics
- **Total Python files**: 72
- **Total lines of code**: ~24,947
- **Largest module**: `analysis/daily_email_analyzer.py` (1,321 LOC)
- **Protocols defined**: 17
- **Exception types**: 10
- **Service container registrations**: 5

### Module Size Distribution
- **Micro (<100 LOC)**: 15 modules
- **Small (100-300 LOC)**: 28 modules
- **Medium (300-600 LOC)**: 21 modules
- **Large (600-1000 LOC)**: 6 modules
- **Very Large (>1000 LOC)**: 2 modules ⚠️

### Dependency Metrics
- **Most imported module**: `core/exceptions.py` (11 imports) ✅
- **Average imports per module**: ~4.2
- **Circular dependencies detected**: 0 ✅
- **Unused protocols**: 0 (all protocols referenced)

### Test Coverage Targets (pyproject.toml)
- **Minimum coverage**: 70%
- **Excluded from coverage**: CLI, fetch, processing, parsers, analysis (most code)
- **Actual coverage**: Unknown (tests not run in this review)
- **Recommendation**: Remove overly broad exclusions, target 80% coverage

---

**Report Generated**: 2026-01-11
**Next Review Recommended**: After implementing Priority 1 fixes (2-3 weeks)
