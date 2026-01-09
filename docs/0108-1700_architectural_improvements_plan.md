# Gmail Fetcher Architectural Improvements Plan

**Created**: 2026-01-08 17:00
**Status**: In Progress
**Priority**: 3-4 (Quality and Architecture Improvements)

---

## Executive Summary

This document outlines the implementation plan for the remaining architectural improvements identified in the master codebase assessment. The focus is on:

1. **Protocol Definitions** - Formal interfaces for Gmail operations
2. **Type Hints** - Comprehensive typing across all public APIs
3. **Dependency Injection** - Decoupled, testable components
4. **Plugin Pattern** - Extensible output and organization strategies
5. **CLI Improvements** - Better command structure with subcommands
6. **Test Coverage** - Achieve 80% coverage target

---

## Task 1: Define Interfaces/Protocols for Gmail Operations

### Location
`src/core/protocols.py`

### Protocol Classes to Create

```python
# GmailClientProtocol - Base operations
- authenticate() -> bool
- get_service() -> Any
- is_authenticated -> bool

# EmailFetcherProtocol - Fetch operations
- search_messages(query: str, max_results: int) -> List[str]
- get_message(message_id: str) -> Optional[Dict[str, Any]]
- download_emails(query: str, max_emails: int, output_dir: str, ...) -> int

# EmailDeleterProtocol - Delete operations
- delete_emails(email_ids: List[str]) -> Dict[str, int]
- trash_emails(email_ids: List[str]) -> Dict[str, int]
- get_email_count(query: str) -> int

# EmailParserProtocol - Parsing operations
- parse_eml(file_path: str) -> Dict[str, Any]
- to_markdown(email_data: Dict[str, Any]) -> str
- clean_html(html_content: str) -> str
```

### Dependencies
- None (foundation task)

---

## Task 2: Add Comprehensive Type Hints

### Target Modules

1. **src/core/**
   - `constants.py` - Already has types
   - `gmail_fetcher.py` - Needs comprehensive typing
   - `gmail_api_client.py` - Needs typing improvements
   - `auth_base.py` - Has types, verify completeness
   - `credential_manager.py` - Add types
   - `protocols.py` (new) - Full typing

2. **src/parsers/**
   - `advanced_email_parser.py` - Has partial types
   - `gmail_eml_to_markdown_cleaner.py` - Add types
   - `robust_eml_converter.py` - Add types

3. **src/handlers/**
   - All handlers need type annotations for args and returns

### Type System Features to Use
- `TypeVar` for generic types
- `Generic[T]` for generic classes
- `Optional[T]` for nullable types
- `Union[A, B]` for multiple types
- `Protocol` for structural subtyping
- `Literal` for string literals

### Deliverable
- `py.typed` marker file in `src/`
- mypy compatibility verified

---

## Task 3: Implement Dependency Injection Container

### Location
`src/core/container.py`

### Injectable Services

```python
# Core Services
CredentialManager - OAuth credential handling
GmailService - Gmail API wrapper
CacheManager - Caching layer
RateLimiter - API rate limiting

# Utility Services
InputValidator - Input validation
ErrorHandler - Error handling

# Parser Services
EmailParser - Email parsing
MarkdownConverter - Markdown conversion
```

### Container Design

```python
class ServiceContainer:
    """DI container for Gmail Fetcher services."""

    def __init__(self):
        self._services: Dict[Type[T], T] = {}
        self._factories: Dict[Type[T], Callable[[], T]] = {}

    def register(self, service_type: Type[T], instance: T) -> None
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None
    def resolve(self, service_type: Type[T]) -> T
    def create_scope(self) -> "ServiceContainer"
```

### Factory Functions

```python
# Factory functions for common configurations
def create_default_container() -> ServiceContainer
def create_readonly_container() -> ServiceContainer
def create_modify_container() -> ServiceContainer
```

---

## Task 4: Refactor to Plugin/Strategy Pattern

### Directory Structure
```
src/
├── plugins/
│   ├── __init__.py
│   ├── base.py          # Base plugin classes
│   ├── output/          # Output format plugins
│   │   ├── __init__.py
│   │   ├── eml.py
│   │   ├── markdown.py
│   │   └── json.py
│   ├── organization/    # File organization plugins
│   │   ├── __init__.py
│   │   ├── by_date.py
│   │   ├── by_sender.py
│   │   └── none.py
│   └── filters/         # Email filter plugins
│       ├── __init__.py
│       └── search.py
└── core/
    └── plugin_registry.py
```

### Plugin Base Classes

```python
# OutputPlugin - Generates output files
class OutputPlugin(ABC):
    name: str
    extension: str

    @abstractmethod
    def generate(self, email_data: Dict[str, Any]) -> str: ...

    @abstractmethod
    def save(self, content: str, path: Path) -> None: ...

# OrganizationPlugin - Organizes file structure
class OrganizationPlugin(ABC):
    name: str

    @abstractmethod
    def get_path(self, email_data: Dict[str, Any], base_dir: Path) -> Path: ...

# FilterPlugin - Filters email results
class FilterPlugin(ABC):
    name: str

    @abstractmethod
    def apply(self, emails: List[Dict]) -> List[Dict]: ...
```

### Plugin Registry

```python
class PluginRegistry:
    """Central registry for all plugins."""

    def register_output(self, plugin: OutputPlugin) -> None
    def register_organization(self, plugin: OrganizationPlugin) -> None
    def register_filter(self, plugin: FilterPlugin) -> None

    def get_output(self, name: str) -> OutputPlugin
    def get_organization(self, name: str) -> OrganizationPlugin
    def get_filter(self, name: str) -> FilterPlugin

    def list_outputs(self) -> List[str]
    def list_organizations(self) -> List[str]
    def list_filters(self) -> List[str]
```

---

## Task 5: Implement Proper CLI with Subcommands

### CLI Structure

```
gmail-fetcher
├── fetch          # Download emails
│   ├── --query
│   ├── --max
│   ├── --output
│   ├── --format
│   └── --organize
├── delete         # Delete emails
│   ├── unread
│   ├── query
│   └── preset
├── analyze        # Analyze emails
│   ├── --input
│   ├── --output
│   └── --format
├── config         # Configuration
│   ├── show
│   ├── setup
│   └── validate
└── auth           # Authentication
    ├── test
    ├── refresh
    └── reset
```

### Directory Structure
```
src/
└── cli/
    ├── __init__.py
    ├── main.py           # Entry point
    ├── fetch.py          # Fetch command
    ├── delete.py         # Delete command
    ├── analyze.py        # Analyze command
    ├── config.py         # Config command
    └── auth.py           # Auth command
```

### Implementation Approach
- Use `argparse` with subparsers (native, no extra dependencies)
- Each command module exposes:
  - `setup_parser(subparsers)` - Configure parser
  - `handle(args)` - Execute command

---

## Task 6: Achieve 80% Test Coverage

### Current Test Structure
```
tests/
├── test_core_gmail_fetcher.py
├── test_parsers_advanced_email.py
├── test_classification_analysis.py
├── ... (23 total test files)
```

### Coverage Gaps to Address

1. **src/core/protocols.py** (new) - Full test coverage needed
2. **src/core/container.py** (new) - Full test coverage needed
3. **src/plugins/** (new) - Full test coverage needed
4. **src/cli/** (new) - Command integration tests

### Test Plan

```python
# Unit tests for protocols
tests/test_core_protocols.py

# Unit tests for DI container
tests/test_core_container.py

# Unit tests for plugins
tests/test_plugins_output.py
tests/test_plugins_organization.py
tests/test_plugins_filters.py

# Integration tests for CLI
tests/test_cli_integration.py
```

### Coverage Target
- Overall: 80%
- New code: 90%
- Critical paths: 95%

---

## Execution Order

1. **Protocols** (Task 1) - Foundation for everything
2. **Type Hints** (Task 2) - Required for protocols
3. **Dependency Injection** (Task 3) - Uses protocols
4. **Plugin Pattern** (Task 4) - Uses DI container
5. **CLI Improvements** (Task 5) - Uses plugins
6. **Test Coverage** (Task 6) - Validates all changes

---

## Success Criteria

- [ ] All protocols defined with full docstrings
- [ ] Type hints on all public functions (mypy clean)
- [ ] DI container with factory functions
- [ ] Plugin system with at least 3 output formats
- [ ] CLI with proper subcommands and help
- [ ] 80% test coverage achieved
- [ ] All existing tests still pass
- [ ] Master assessment updated with completed items

---

## Risk Mitigation

1. **Backward Compatibility** - Keep existing APIs, add new ones
2. **Test Coverage** - Write tests for each component before integration
3. **Incremental Changes** - Commit after each task completion
4. **Documentation** - Update CLAUDE.md with new patterns

---

*Implementation Plan Version 1.0*
*Created by Multi-Agent Orchestrator*
