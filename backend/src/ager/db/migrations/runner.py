"""Simple migration runner for AGER database."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def apply_migrations(db_path: Path, migrations_dir: Path) -> None:
    """Apply all pending SQL migrations to the database.

    Args:
        db_path: Path to the SQLite database file
        migrations_dir: Directory containing .sql migration files

    The runner:
    - Creates a schema_migrations table to track applied migrations
    - Applies migrations in alphabetical order (0001_*.sql, 0002_*.sql, etc.)
    - Skips already-applied migrations (idempotent)
    """
    # Ensure database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect and create migrations tracking table
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)")

    # Get list of already-applied migrations
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}

    # Apply pending migrations
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        version = sql_file.stem
        if version in applied:
            continue

        # Read and execute migration
        sql_content = sql_file.read_text(encoding="utf-8")
        with conn:
            conn.executescript(sql_content)
            conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))

    conn.close()
