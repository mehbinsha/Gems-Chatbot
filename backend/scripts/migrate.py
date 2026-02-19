import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "backend" / "app.db"
MIGRATIONS_DIR = BASE_DIR / "backend" / "migrations"


def ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL UNIQUE,
            applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def already_applied(conn: sqlite3.Connection, version: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM schema_migrations WHERE version = ? LIMIT 1", (version,)
    ).fetchone()
    return row is not None


def apply_migrations() -> None:
    conn = sqlite3.connect(DB_PATH)
    ensure_migrations_table(conn)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for file_path in migration_files:
        version = file_path.name
        if already_applied(conn, version):
            print(f"Skipping {version} (already applied)")
            continue

        sql = file_path.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
        conn.commit()
        print(f"Applied {version}")

    conn.close()
    print(f"Database ready: {DB_PATH}")


if __name__ == "__main__":
    apply_migrations()
