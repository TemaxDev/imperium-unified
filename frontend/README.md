# Frontend Imperium

Interface web moderne pour Imperium - React 19 + Vite + Tailwind CSS.

## Stack

- React 19 (UI)
- Vite (Build tool)
- TypeScript (Type safety)
- Tailwind CSS (Styling)
- Zustand (State management)
- Vitest (Testing)

## Installation

```bash
# Installer les dépendances
npm install
```

## Développement

```bash
# Lancer le serveur de développement
npm run dev

# Lancer les tests
npm run test

# Lancer le linter
npm run lint

# Formatter le code
npm run format

# Vérifier les types
npm run type-check

# Build production
npm run build
```

## Structure

```
frontend/
├── src/
│   ├── components/    # Composants réutilisables
│   ├── pages/         # Pages de l'application
│   ├── services/      # Services API
│   ├── stores/        # Stores Zustand
│   ├── test/          # Configuration des tests
│   ├── App.tsx        # Composant racine
│   └── main.tsx       # Point d'entrée
├── index.html         # Template HTML
├── package.json       # Dépendances
└── vite.config.ts     # Configuration Vite
```

## Normes

- TypeScript strict mode
- ESLint + Prettier
- Conventional Commits
- Coverage > 80%
