# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0-A8] - 2025-10-23

### Added
- **AI Diplomacy Layer (A8)**: Deterministic AI diplomacy system with opinion dynamics, stance computation, and treaty management
- **Diplomacy Rules v1 (diplo_v1)**: Versioned rules with calibrated constants for 30-60min gameplay
  - Opinion cooldown: `opinion *= 0.98` per game-hour (decay towards 0)
  - Attack penalty: `-20` opinion per aggression
  - Trade bonus: `+8` opinion per trade transaction
  - Honor bonus: `+1.5` opinion per hour of active alliance
  - Stance thresholds: ALLY (≥40), HOSTILE (≤-40), NEUTRAL otherwise
- **Evaluator Service**: Time-based opinion/stance updates with treaty expiration
  - Opinion cooldown (multiplicative decay)
  - Stance recomputation based on opinion + treaty locks
  - Treaty expiration handling
  - Honor bonuses for active alliances
- **Proposer Service**: Deterministic AI suggestions with integer scoring
  - CEASEFIRE: suggested for HOSTILE stance + recent attacks
  - TRADE: suggested for NEUTRAL stance + recent trades (blocked if already active)
  - ALLIANCE: suggested for high opinion (≥20) + shared enemies
  - Tie-breaker: stable ordering by TYPE_RANK (CEASEFIRE < TRADE < ALLIANCE)
- **TreatyService**: Treaty proposal and lifecycle management
  - Immediate stance/opinion adjustments on treaty opening
  - CEASEFIRE: calms HOSTILE → NEUTRAL, adds opinion boost
  - TRADE: no stance lock (benefits via trade events)
  - ALLIANCE: locks stance to ALLY, ensures opinion ≥ ally_threshold
  - Idempotent duplicate detection
- **Diplomacy Migrations**: SQL migrations 0006-0007 for factions, relations, treaties, events tables
  - Relations normalized with `CHECK (a < b)` constraint
  - Treaties track status (ACTIVE/EXPIRED/CANCELLED)
  - Events log for audit trail
- **Diplomacy Persistence**: Extended Memory/File/SQL engines with diplomacy structures
  - DiploStore protocol with normalize_pair() helper
  - MemoryDiploStore, FileDiploStore, SQLDiploStore implementations
  - Auto-saves for FileEngine, transactions for SQLEngine
- **Internal API Endpoints**:
  - `POST /ai/diplomacy/tick`: Apply time-based diplomacy updates
  - `GET /ai/diplomacy/suggest?a=X&b=Y&k=3`: Get top-k AI suggestions
  - `POST /ai/diplomacy/propose`: Propose treaty between factions
  - `GET /ai/diplomacy/rules`: Expose diplomacy rules constants
- **Diplomacy DTOs**: Type-safe data transfer objects with Literal types
  - StanceType, TreatyType, TreatyStatus
  - Faction, Relation, Treaty, DiplomacyEvent, Suggestion
- **ORM Models**: Added Faction, Relation, Treaty, DiplomacyEvent models for SQL adapter
- **Comprehensive Tests**: 41 tests across 5 test files
  - Rules coherence (stance thresholds, treaty locks, cooldown)
  - Tick updates (cooldown, expiration, events)
  - Proposer suggestions (deterministic scoring, tie-breaking)
  - Treaty flow (propose → active → expire)
  - API endpoints (HTTP 200, schemas, determinism)

### Changed
- **Non-breaking**: Existing gameplay (A7) and simulation (A4-A6) APIs unchanged
- **Architecture**: DiplomacyService sits above existing engine layer (no port modifications)
- **Test Coverage**: 41 new tests, A8 services near 100% coverage

### Fixed
- **Deterministic Scoring**: All suggestion scores use integers (fixed-point) for cross-platform consistency
- **Pair Normalization**: Relations always stored with `a < b` regardless of API call order
- **Idempotence**: Duplicate treaty proposals rejected with clear reason

## [0.7.0-A7] - 2025-10-23

### Added
- **Gameplay Engine (A7)**: Deterministic tick-based gameplay system built on top of existing ports/adapters
- **Production System**: Resource accrual based on building levels and time delta (Δt)
  - Formula: `production = floor(rate(level) * Δt_hours)` where `rate(level) = base * 1.15^(level-1)`
  - Idempotent: same `now` parameter produces empty delta on second call
  - Tracks `last_tick` per village in `engine_state` table/structure
- **Build System**: Single-queue build management per village
  - Deducts resources at enqueue time
  - Calculates ETA based on building level: `duration_s(level) = base * 1.32^(level-1)`
  - Completes builds when `ETA <= now`, increments building level
  - Cost formula: `cost(level) = base * 1.28^(level-1)`
- **GameplayService**: Orchestrates tick execution (Production → Build systems)
- **Gameplay Rules v1**: Versioned rules with configurable base rates, costs, and durations
- **Gameplay Migrations**: SQL migrations 0003-0005 for `buildings` and `engine_state` tables
- **Gameplay Persistence**: Extended MemoryEngine and FileStorageEngine with buildings/engineState structures
- **Internal API Endpoints**:
  - `POST /cmd/tick`: Execute gameplay tick (accepts optional ISO datetime `now` parameter)
  - `GET /rules`: Expose current gameplay rules (version, rates, costs, durations)
- **Clock Abstractions**: `SystemClock` and `FixedClock` for deterministic testing
- **Resource Deltas**: `ResourceDelta` and `SnapshotDelta` for tracking state changes
- **Gameplay Tests**: 23 comprehensive tests covering rules, production, builds, idempotence, and API
- **ORM Models**: Added `Building` and `EngineState` models for SQL adapter

### Changed
- **Engine Adapters**: Non-breaking extension with gameplay persistence (buildings, engine_state)
- **Existing API**: `/cmd/build` behavior unchanged - maintains same response format (non-breaking)
- **Test Coverage**: Increased to 64% overall with 89-96% coverage on gameplay systems

### Fixed
- **Idempotence**: Tick with same `now` parameter produces empty delta (deterministic)
- **Build Completion**: No duplicate completions when multiple ticks occur after ETA

## [0.6.3-A6-ci] - 2025-10-22

### Added
- **AGER Ports/Adapters Architecture**: Implemented hexagonal architecture with `SimulationEngine` port and `MemoryEngine` adapter for clean separation of concerns
- **SQLiteEngine with ORM**: Persistent adapter using SQLite database with SQLModel ORM for world state (selectable via `AGER_ENGINE=sql`)
- **ORM Layer**: SQLModel (SQLAlchemy 2.0 + Pydantic) models for `Village`, `Resources`, and `BuildQueue` tables
- **Migration System**: Simple SQL migration runner with versioning (`schema_migrations` table, idempotent, alphabetical order)
- **Migration Files**: `0001_init.sql` (schema DDL), `0002_seed.sql` (initial data seed)
- **Session Management**: Dynamic engine cache by db_path in `db/session.py` with `get_session()` and `get_engine()` helpers
- **FileStorageEngine**: Persistent adapter using JSON file storage for world state (selectable via `AGER_ENGINE` env var)
- **Seed Tool**: CLI tool `python -m tools.seed_file_storage` to initialize FileStorageEngine state with sample data
- **Settings Module**: Configuration management with `get_engine_type()`, `get_storage_path()`, and `get_db_path()` (env: `AGER_ENGINE`, `AGER_STORAGE_PATH`, `AGER_DB_PATH`)
- **Dependency Injection**: Enhanced `container.py` with dynamic engine selection based on environment configuration (memory/file/sql)
- **Contract Tests**: 10 implementation-agnostic tests in `tests/ports/` validating `SimulationEngine` interface
- **DTO Models**: Extracted DTOs (`Village`, `Resources`, `BuildCmd`) into dedicated `models.py` module to resolve circular dependencies
- **Unit Tests**: Added `test_engine_memory.py` (3 tests), `test_file_engine.py` (9 tests), `test_seed_file_storage.py` (9 tests), `test_engine_sql.py` (8 tests), `test_engine_sql_orm.py` (7 tests), `test_migrations_runner.py` (3 tests), and contract tests (10 tests)
- **API Error Tests**: Added `test_api_errors.py` covering 404 (village not found) and 422 (invalid command) scenarios

### Changed
- **SQLiteEngine**: Complete refactor from raw SQL to ORM-based implementation using SQLModel sessions
- **Database Schema**: Renamed table `villages` → `village` to match SQLModel conventions
- **Container**: Refactored to support multiple engine implementations (memory/file/sql) with `_create_engine()` factory and `reset_engine()` for tests
- **Settings**: Extended `EngineType` to include "sql" and added `get_db_path()` helper
- **FileStorageEngine**: Enhanced to support dual-format JSON (legacy inline resources + new separated resources/buildQueues)
- **API Rewiring**: Updated `app.py` to use `get_engine()` dependency injection instead of direct state access
- **Dependencies**: Added `sqlmodel>=0.0.27` to project dependencies in pyproject.toml
- **Code Quality**: Migrated Ruff configuration to `[tool.ruff.lint]` section (new format)
- **Test Coverage**: Improved to 93% with 55 tests total (45 previous + 10 ORM/migrations)
- **CI Workflows**: Complete refactor to modern practices with matrix testing, concurrency control, and coverage enforcement
  - **Backend CI**: Matrix testing across all 3 implementations (memory/file/sql) with pytest contract tests
  - **Frontend CI**: Added matrix support (Node 20), concurrency control, and timeout limits
  - **CodeQL**: Added concurrency control and timeout limits (20min)
  - **PR Checks**: Added concurrency control and timeout limits (5min)
  - **Branch Migration**: All workflows migrated from `master` → `main` branch
  - **Timeouts**: backend 15min, frontend 10min to prevent hanging jobs
  - **Concurrency**: `cancel-in-progress: true` for all workflows to stop obsolete jobs
  - **Coverage Gate**: Enforced 90% minimum coverage with `--cov-fail-under=90`
  - **Artifacts**: Upload coverage reports per implementation for debugging

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
