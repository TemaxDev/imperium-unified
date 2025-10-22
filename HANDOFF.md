# HANDOFF — Imperium Unified

## Repo & branches

- Repo: https://github.com/TemaxDev/imperium-unified
- Branch active: feat/A4-5-file-storage-engine (FileStorageEngine + Contract Tests)

## Environnement

- Python: conda env `imperium312` (3.12)
- Variables d'environnement:
  - `AGER_ENGINE`: Type de moteur ("memory" ou "file", défaut: "memory")
  - `AGER_STORAGE_PATH`: Chemin du fichier JSON pour FileStorageEngine (défaut: "./data/world.json")
  - `TEST_ENGINE_IMPL`: Type de moteur pour tests de contrat ("memory" ou "file", défaut: "memory")
- Démarrer:
  ```bash
  conda activate imperium312
  cd backend
  pytest -q
  # Avec memory engine (défaut)
  uvicorn ager.app:app --reload --app-dir src
  # Avec file engine
  AGER_ENGINE=file uvicorn ager.app:app --reload --app-dir src
  ```

## État technique

- Backend: FastAPI ok → routes `/health`, `/snapshot`, `/village/{id}`, `/cmd/build`
- Architecture: Ports/Adapters (SimulationEngine + MemoryEngine + FileStorageEngine)
- Tests: 28 verts (19 anciens + 9 FileStorageEngine), couverture 95%
- Frontend: Vite/React structuré (non branché)
- CI: backend, frontend, PR checks, CodeQL

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

## ✅ Mission A4-5 – FileStorageEngine (EN COURS)

**Status:** 🚧 En cours (branche feat/A4-5-file-storage-engine)

**Livrables:**
- `backend/src/ager/settings.py` — Configuration (AGER_ENGINE, AGER_STORAGE_PATH)
- `backend/src/ager/adapters/file_engine.py` — FileStorageEngine (persistance JSON)
- `backend/src/ager/container.py` — Sélection dynamique du moteur
- `backend/tests/test_file_engine.py` — 9 tests unitaires
- `backend/tests/ports/` — Tests de contrat agnostiques (TEST_ENGINE_IMPL)

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

## Prochaines missions

À définir avec Chef Dev après merge de la PR A4-5.
