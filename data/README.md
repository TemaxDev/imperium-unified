# Données de jeu Imperium

Ce dossier contient toutes les données de jeu au format JSON normalisé.

## Structure prévue

```
data/
├── README.md              # Ce fichier
├── peoples/               # 5 peuples jouables
├── units/                 # 50+ unités militaires
├── buildings/             # 29 bâtiments
└── formulas/              # Formules de calcul
```

## Format

Toutes les données sont en **JSON normalisé** et respectent un schéma strict validé par Pydantic.

### Exemple - Peuple

```json
{
  "id": "romans",
  "name": "Romains",
  "description": "Peuple équilibré, excellents défenseurs",
  "bonuses": {
    "defense": 1.15,
    "construction_speed": 1.0
  }
}
```

---

**Mission A3 :** Import complet des données JSON
