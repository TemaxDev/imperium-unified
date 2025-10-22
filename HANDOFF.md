# HANDOFF — Imperium Unified

## Repo & branches

- Repo: https://github.com/TemaxDev/imperium-unified
- Branch active: feat/A6-2-orm-and-migrations (ORM + Migrations)

## Environnement

- Python: conda env `imperium312` (3.12)
- Variables d'environnement:
  - `AGER_ENGINE`: Type de moteur ("memory", "file" ou "sql", défaut: "memory")
  - `AGER_STORAGE_PATH`: Chemin du fichier JSON pour FileStorageEngine (défaut: "./data/world.json")
  - `AGER_DB_PATH`: Chemin de la base SQLite pour SQLiteEngine (défaut: "./data/ager.db")
  - `TEST_ENGINE_IMPL`: Type de moteur pour tests de contrat ("memory", "file" ou "sql", défaut: "memory")
- Démarrer:
  ```bash
  conda activate imperium312
  cd backend
  pytest -q
  # Avec memory engine (défaut)
  uvicorn ager.app:app --reload --app-dir src
  # Avec file engine
  AGER_ENGINE=file uvicorn ager.app:app --reload --app-dir src
  # Avec SQL engine
  AGER_ENGINE=sql uvicorn ager.app:app --reload --app-dir src
  ```

## État technique

- Backend: FastAPI ok → routes `/health`, `/snapshot`, `/village/{id}`, `/cmd/build`
- Architecture: Ports/Adapters (SimulationEngine + MemoryEngine + FileStorageEngine + SQLiteEngine avec ORM)
- ORM: SQLModel (SQLAlchemy 2.0) pour SQLiteEngine
- Migrations: Système SQL simple avec versioning
- Tests: 55 verts (45 précédents + 10 ORM/migrations), couverture 93%
- Frontend: Vite/React structuré (non branché)
- CI: backend, frontend, PR checks, CodeQL + contract tests avec FileStorageEngine + SQLiteEngine

## ✅ Mission A4-3 – Adaptateur AGER (COMPLÉTÉE)

**Status:** ✅ Done (PR en cours vers main)

**Livrables:**
- `backend/src/ager/models.py` — DTOs (Village, Resources, BuildCmd)
- `backend/src/ager/ports.py` — Port `SimulationEngine` (Protocol)
- `backend/src/ager/adapters/memory_engine.py` — Implémentation in-memory
- `backend/src/ager/container.py` — Conteneur DI `get_engine()`
- `backend/src/ager/app.py` — Rewiring (utilise `get_engine()`)
- `backend/tests/test_engine_memory.py` — 3 tests unitaires
- `backend/tests/test_api_errors.py` — Tests API 404/422

**Résultats:**
- ✅ Tests verts: 9/9
- ✅ Couverture: 95% (> 90%)
- ✅ JSON contract: identique
- ✅ Pas de state global: injection via `get_engine()`
- ✅ MyPy: validé
- ✅ Ruff/Black: OK

**Architecture:** Ports/Adapters → pas de state global, JSON contract verrouillé.

## ✅ Mission A4-4 – Contract Tests (COMPLÉTÉE)

**Status:** ✅ Done (PR #2)

**Livrables:**
- `backend/tests/ports/conftest.py` — Fixture engine avec TEST_ENGINE_IMPL
- `backend/tests/ports/test_simulation_engine_contract.py` — 10 tests de contrat

**Résultats:**
- ✅ Tests: 10 contract tests agnostiques
- ✅ Passent avec MemoryEngine ET FileStorageEngine
- ✅ Isolation: chaque test obtient une instance fraîche

## ✅ Mission A4-5 – FileStorageEngine (COMPLÉTÉE)

**Status:** ✅ Done (PR #3)

**Livrables:**
- `backend/src/ager/settings.py` — Configuration (AGER_ENGINE, AGER_STORAGE_PATH)
- `backend/src/ager/adapters/file_engine.py` — FileStorageEngine (persistance JSON)
- `backend/src/ager/container.py` — Sélection dynamique du moteur
- `backend/tests/test_file_engine.py` — 9 tests unitaires
- `backend/tests/ports/conftest.py` — Adapté pour TEST_ENGINE_IMPL

**Résultats:**
- ✅ Tests: 28 verts (19 anciens + 9 nouveaux)
- ✅ Couverture: 95% (> 90%)
- ✅ Contract tests passent avec memory ET file
- ✅ MyPy: validé
- ✅ Ruff/Black: OK
- ✅ API inchangée

**Configuration:**
- `AGER_ENGINE=memory` (défaut) → MemoryEngine
- `AGER_ENGINE=file` → FileStorageEngine
- `AGER_STORAGE_PATH=./data/world.json` (défaut)

## ✅ Mission A6-1 – SQLiteEngine (COMPLÉTÉE)

**Status:** ✅ Done (PR en cours, branche feat/A6-1-sqlite-engine)

**Livrables:**
- `backend/src/ager/adapters/sql_engine.py` — SQLiteEngine (persistance SQLite)
- `backend/src/ager/settings.py` — Ajout AGER_DB_PATH + "sql" à EngineType
- `backend/src/ager/container.py` — Support du cas "sql"
- `backend/tests/test_engine_sql.py` — 8 tests unitaires
- `backend/tests/ports/conftest.py` — Support TEST_ENGINE_IMPL=sql

**Résultats:**
- ✅ Tests: 45 verts (37 précédents + 8 nouveaux)
- ✅ Couverture: 92% (> 90%)
- ✅ Contract tests passent avec memory, file ET sql
- ✅ MyPy: validé
- ✅ Ruff/Black: OK
- ✅ API inchangée

**Configuration:**
- `AGER_ENGINE=memory` (défaut) → MemoryEngine
- `AGER_ENGINE=file` → FileStorageEngine
- `AGER_ENGINE=sql` → SQLiteEngine
- `AGER_DB_PATH=./data/ager.db` (défaut)

**Schéma SQLite:**
- Table `villages`: id, name
- Table `resources`: village_id, wood, clay, iron, crop
- Table `build_queue`: id, village_id, building, level, queued_at
- Seed automatique: village 1 "Capitale" avec 800 de chaque ressource

## ✅ Mission A5-2 – File Storage Seeding & Validation (COMPLÉTÉE)

**Status:** ✅ Done (PR #4, branche feat/A5-2-file-seed-and-validation)

**Livrables:**
- `backend/tools/seed_file_storage.py` — Script CLI de seed avec argparse
- `backend/tests/test_seed_file_storage.py` — 9 tests de validation du seed
- `backend/src/ager/adapters/file_engine.py` — Support dual-format JSON (legacy + seed)
- `.github/workflows/backend-ci.yml` — CI step pour TEST_ENGINE_IMPL=file

**Résultats:**
- ✅ Tests: 37 verts (28 précédents + 9 seed validation)
- ✅ Couverture: 94% (> 90%)
- ✅ Seed tool fonctionnel: `python -m tools.seed_file_storage [--path custom/path.json]`
- ✅ Dual-format: compatibilité arrière avec resources inline + nouveau format séparé
- ✅ CI validé avec contract tests (TEST_ENGINE_IMPL=file)
- ✅ MyPy: validé
- ✅ Ruff/Black: OK
- ✅ Fix encoding Windows (emojis → plain text)

**Format seed JSON:**
```json
{
  "villages": {"1": {"id": 1, "name": "Capitale"}},
  "resources": {"1": {"wood": 100, "clay": 80, "iron": 90, "crop": 75}},
  "buildQueues": {"1": [{"building": "farm", "level": 2, "queuedAt": "..."}]}
}
```

## ✅ Mission A6-2 – ORM & Migrations (COMPLÉTÉE)

**Status:** ✅ Done (PR en cours, branche feat/A6-2-orm-and-migrations)

**Livrables:**
- `backend/src/ager/db/models.py` — Modèles ORM SQLModel (Village, Resources, BuildQueue)
- `backend/src/ager/db/session.py` — Gestion session/engine avec cache par db_path
- `backend/src/ager/db/migrations/0001_init.sql` — Schéma initial DDL
- `backend/src/ager/db/migrations/0002_seed.sql` — Seed minimal (village 1)
- `backend/src/ager/db/migrations/runner.py` — Runner de migrations SQL
- `backend/src/ager/adapters/sql_engine.py` — Refactored vers ORM (session-based)
- `backend/tests/test_engine_sql_orm.py` — 7 tests ORM
- `backend/tests/test_migrations_runner.py` — 3 tests migrations
- `backend/pyproject.toml` — Ajout dépendance sqlmodel>=0.0.27

**Résultats:**
- ✅ Tests: 55 verts (45 précédents + 10 nouveaux)
- ✅ Couverture: 93% (> 90%)
- ✅ Contract tests A4-4 inchangés (memory/file/sql passent)
- ✅ MyPy: validé
- ✅ Ruff/Black: OK
- ✅ API contrat 100% identique (zéro breaking change)

**Architecture ORM:**
- SQLModel (basé sur SQLAlchemy 2.0 + Pydantic)
- Session par db_path (cache d'engines)
- Migrations SQL versionnées (`schema_migrations` table)
- Tables: `village`, `resources`, `build_queue`

**Migrations:**
- `0001_init.sql`: Crée les tables
- `0002_seed.sql`: Insert village 1 "Capitale"
- Runner idempotent (skip déjà appliquées)
- Ordre alphabétique garanti

## Prochaines missions

À définir avec Chef Dev après consolidation et merge des PRs.
