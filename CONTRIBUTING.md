# Guide de Contribution

Merci de votre intérêt pour contribuer à Imperium !

## Processus de développement

### 1. Workflow Git

```bash
# Créer une branche depuis master
git checkout master
git pull origin master
git checkout -b feat/A2-votre-feature

# Faire vos modifications
# ...

# Commit avec Conventional Commits
git add .
git commit -m "feat: ajout de la fonctionnalité X"

# Push et créer une PR
git push -u origin feat/A2-votre-feature
```

### 2. Conventions de nommage

#### Branches
- `feat/<num>-<description>` : Nouvelle fonctionnalité
- `fix/<num>-<description>` : Correction de bug
- `refactor/<zone>` : Refactoring
- `docs/<sujet>` : Documentation
- `release/vX.Y.Z` : Préparation release

#### Commits (Conventional Commits)
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation uniquement
- `style:` Formatage (sans changement de code)
- `refactor:` Refactoring (ni feature ni fix)
- `test:` Ajout/modification de tests
- `chore:` Maintenance, dépendances

### 3. Standards de qualité

#### Backend (Python)
```bash
ruff check .          # Linting
black .               # Formatting
mypy src/             # Type checking
pytest                # Tests
```

#### Frontend (TypeScript/React)
```bash
npm run lint          # ESLint
npm run format        # Prettier
npm run type-check    # TypeScript
npm test              # Tests
npm run build         # Build
```

### 4. Pull Requests

**Checklist obligatoire :**
- [ ] Code formaté (Black/Prettier)
- [ ] Lint OK (Ruff/ESLint)
- [ ] Types OK (MyPy/TypeScript)
- [ ] Tests passent
- [ ] Coverage > 80%
- [ ] Conventional Commits

---

**Merci de maintenir la qualité AAA d'Imperium !**
