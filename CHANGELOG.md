# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **AGER Ports/Adapters Architecture**: Implemented hexagonal architecture with `SimulationEngine` port and `MemoryEngine` adapter for clean separation of concerns
- **FileStorageEngine**: Persistent adapter using JSON file storage for world state (selectable via `AGER_ENGINE` env var)
- **Seed Tool**: CLI tool `python -m tools.seed_file_storage` to initialize FileStorageEngine state with sample data
- **Settings Module**: Configuration management with `get_engine_type()` and `get_storage_path()` (env: `AGER_ENGINE`, `AGER_STORAGE_PATH`)
- **Dependency Injection**: Enhanced `container.py` with dynamic engine selection based on environment configuration
- **Contract Tests**: 10 implementation-agnostic tests in `tests/ports/` validating `SimulationEngine` interface
- **DTO Models**: Extracted DTOs (`Village`, `Resources`, `BuildCmd`) into dedicated `models.py` module to resolve circular dependencies
- **Unit Tests**: Added `test_engine_memory.py` (3 tests), `test_file_engine.py` (9 tests), `test_seed_file_storage.py` (9 tests), and contract tests (10 tests)
- **API Error Tests**: Added `test_api_errors.py` covering 404 (village not found) and 422 (invalid command) scenarios

### Changed
- **Container**: Refactored to support multiple engine implementations with `_create_engine()` factory and `reset_engine()` for tests
- **FileStorageEngine**: Enhanced to support dual-format JSON (legacy inline resources + new separated resources/buildQueues)
- **API Rewiring**: Updated `app.py` to use `get_engine()` dependency injection instead of direct state access
- **Code Quality**: Migrated Ruff configuration to `[tool.ruff.lint]` section (new format)
- **Test Coverage**: Maintained at 94% with 37 tests total
- **CI**: Added contract test validation with FileStorageEngine (`TEST_ENGINE_IMPL=file`)

### Fixed
- **Circular Import**: Resolved circular dependency between `app.py`, `container.py`, and `memory_engine.py` by extracting DTOs

## [0.1.0-alpha] - 2025-01-XX

### Added
- Initial FastAPI backend structure with `/health`, `/snapshot`, `/village/{id}`, `/cmd/build` endpoints
- React 19 + Vite frontend skeleton
- CI/CD workflows (backend, frontend, PR checks, CodeQL)
- Test suite with pytest + httpx (ASGITransport)
- Code quality tools: Ruff, Black, MyPy
- Development environment with Python 3.12
