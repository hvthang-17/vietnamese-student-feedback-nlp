"""Connection-per-operation SQLite adapter with explicit transaction boundaries."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .migrations import MIGRATIONS, migrate


class Database:
    def __init__(self, path: Path, timeout: float = 5.0):
        self.path = Path(path)
        self.timeout = timeout

    @contextmanager
    def connection(self):
        # No global connection: each operation owns its thread-local connection.
        conn = sqlite3.connect(self.path, timeout=self.timeout, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self, write: bool = False):
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            try:
                yield conn
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction(write=True) as conn:
            migrate(conn)

    def verify_schema(self):
        if not self.path.is_file():
            raise RuntimeError("Database is missing; run migrations before starting the API")
        with self.connection() as conn:
            versions = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
            if versions != {version for version, _, _ in MIGRATIONS}:
                raise RuntimeError("Database migrations are required")

    def ping(self) -> bool:
        try:
            if not self.path.is_file():
                return False
            with self.connection() as conn:
                conn.execute("SELECT 1").fetchone()
            return True
        except sqlite3.Error:
            return False
