# Backend Imperium

API REST basée sur FastAPI + Moteur ECS AGER.

## Stack

- Python 3.12+
- FastAPI (API REST)
- AGER (Advanced Game Engine Runtime - ECS custom)
- PyTest (tests)

## Installation

```bash
# Installer les dépendances
pip install -e .

# Installer les dépendances de développement
pip install -e ".[dev]"
```

## Structure

```
backend/
├── src/
│   └── ager/          # Moteur ECS
├── tests/             # Tests unitaires et intégration
├── pyproject.toml     # Configuration du projet
└── README.md
```

## Développement

```bash
# Lancer les tests
pytest

# Linter
ruff check .

# Formatter
black .

# Type checking
mypy src/
```

## Normes

- Conventional Commits
- Type hints obligatoires (mypy strict)
- Coverage > 80%
- Ruff + Black + MyPy pour la qualité
