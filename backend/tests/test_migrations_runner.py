"""Tests for the migrations runner."""

import sqlite3

from ager.db.migrations.runner import apply_migrations


def test_runner_applies_only_new_migrations(tmp_path):
    """Test que le runner applique uniquement les nouvelles migrations."""
    db_path = tmp_path / "test.db"
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()

    # Créer une première migration
    (migrations_dir / "0001_first.sql").write_text(
        "CREATE TABLE test_table (id INTEGER PRIMARY KEY);", encoding="utf-8"
    )

    # Appliquer la première migration
    apply_migrations(db_path, migrations_dir)

    # Vérifier que la table existe
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
    assert cursor.fetchone() is not None

    # Vérifier que la migration est enregistrée
    cursor = conn.execute("SELECT version FROM schema_migrations")
    versions = {row[0] for row in cursor.fetchall()}
    assert "0001_first" in versions
    conn.close()

    # Créer une deuxième migration
    (migrations_dir / "0002_second.sql").write_text(
        "CREATE TABLE test_table2 (id INTEGER PRIMARY KEY);", encoding="utf-8"
    )

    # Appliquer les migrations (seule la deuxième devrait être appliquée)
    apply_migrations(db_path, migrations_dir)

    # Vérifier que les deux tables existent
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name IN ('test_table', 'test_table2')"
    )
    tables = {row[0] for row in cursor.fetchall()}
    assert "test_table" in tables
    assert "test_table2" in tables

    # Vérifier que les deux migrations sont enregistrées
    cursor = conn.execute("SELECT version FROM schema_migrations")
    versions = {row[0] for row in cursor.fetchall()}
    assert "0001_first" in versions
    assert "0002_second" in versions
    conn.close()


def test_runner_is_idempotent(tmp_path):
    """Test que le runner est idempotent (peut être appelé plusieurs fois)."""
    db_path = tmp_path / "test.db"
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()

    # Créer une migration
    (migrations_dir / "0001_test.sql").write_text(
        "CREATE TABLE idempotent_test (id INTEGER PRIMARY KEY);", encoding="utf-8"
    )

    # Appliquer la migration plusieurs fois
    apply_migrations(db_path, migrations_dir)
    apply_migrations(db_path, migrations_dir)
    apply_migrations(db_path, migrations_dir)

    # Vérifier qu'il n'y a qu'une seule entrée dans schema_migrations
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT COUNT(*) FROM schema_migrations WHERE version='0001_test'")
    count = cursor.fetchone()[0]
    assert count == 1

    # Vérifier que la table existe
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='idempotent_test'"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_migrations_applied_in_order(tmp_path):
    """Test que les migrations sont appliquées dans l'ordre alphabétique."""
    db_path = tmp_path / "test.db"
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()

    # Créer des migrations dans le désordre
    (migrations_dir / "0003_third.sql").write_text(
        "INSERT INTO migration_order VALUES (3);", encoding="utf-8"
    )
    (migrations_dir / "0001_first.sql").write_text(
        "CREATE TABLE migration_order (step INTEGER);", encoding="utf-8"
    )
    (migrations_dir / "0002_second.sql").write_text(
        "INSERT INTO migration_order VALUES (2);", encoding="utf-8"
    )

    # Appliquer les migrations
    apply_migrations(db_path, migrations_dir)

    # Vérifier que les migrations ont été appliquées dans le bon ordre
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT step FROM migration_order ORDER BY step")
    steps = [row[0] for row in cursor.fetchall()]
    assert steps == [2, 3]  # 2 puis 3 (car 1 crée juste la table)
    conn.close()
