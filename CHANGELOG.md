# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **AGER Ports/Adapters Architecture**: Implemented hexagonal architecture with `SimulationEngine` port and `MemoryEngine` adapter for clean separation of concerns
- **Dependency Injection**: Added `container.py` with `get_engine()` factory function for proper DI pattern
- **DTO Models**: Extracted DTOs (`Village`, `Resources`, `BuildCmd`) into dedicated `models.py` module to resolve circular dependencies
- **Unit Tests**: Added `test_engine_memory.py` with 3 test cases covering snapshot, get_village, and queue_build operations
- **API Error Tests**: Added `test_api_errors.py` covering 404 (village not found) and 422 (invalid command) scenarios

### Changed
- **API Rewiring**: Updated `app.py` to use `get_engine()` dependency injection instead of direct state access
- **Code Quality**: Migrated Ruff configuration to `[tool.ruff.lint]` section (new format)
- **Test Coverage**: Improved to 95% (65 statements, 3 misses in Protocol interface)

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
