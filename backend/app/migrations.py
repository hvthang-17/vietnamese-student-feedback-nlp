"""Append-only, transactional SQLite migrations. Never edit an applied revision."""
from datetime import datetime, timezone
import sqlite3

from .domain.models import utc_timestamp

LATEST_VERSION = 2


def initial(conn: sqlite3.Connection) -> None:
    """Adopt the original schema without dropping any existing records."""
    statements = [
        """CREATE TABLE IF NOT EXISTS feedback_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'manual', created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, feedback_id INTEGER NOT NULL UNIQUE,
            sentiment_label TEXT NOT NULL, sentiment_confidence REAL NOT NULL,
            topic_label TEXT NOT NULL, topic_confidence REAL NOT NULL,
            model_version TEXT NOT NULL, predicted_at TEXT NOT NULL,
            FOREIGN KEY(feedback_id) REFERENCES feedback_records(id))""",
    ]
    for statement in statements:
        conn.execute(statement)


def normalized_time(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        # Legacy generated timestamps were Ho Chi Minh local time; document this assumption.
        from datetime import timedelta
        parsed = parsed.replace(tzinfo=timezone(timedelta(hours=7)))
    return utc_timestamp(parsed)


def feedback_metadata(conn: sqlite3.Connection) -> None:
    """Rebuild with constraints; preserve IDs and legacy normalized content."""
    sequences = dict(conn.execute("SELECT name,seq FROM sqlite_sequence"))
    conn.execute("""CREATE TABLE feedback_records_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_text TEXT NOT NULL CHECK(length(raw_text) BETWEEN 1 AND 5000),
        text TEXT NOT NULL CHECK(length(trim(text)) BETWEEN 1 AND 5000),
        source TEXT NOT NULL CHECK(source IN ('manual','batch','csv')),
        created_at TEXT, received_at TEXT NOT NULL)""")
    conn.execute("""CREATE TABLE predictions_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feedback_id INTEGER NOT NULL UNIQUE REFERENCES feedback_records_v2(id) ON DELETE CASCADE,
        sentiment_label TEXT NOT NULL CHECK(sentiment_label IN ('negative','neutral','positive')),
        sentiment_confidence REAL NOT NULL CHECK(sentiment_confidence BETWEEN 0 AND 1),
        topic_label TEXT NOT NULL CHECK(topic_label IN ('lecturer','training_program','facility','others')),
        topic_confidence REAL NOT NULL CHECK(topic_confidence BETWEEN 0 AND 1),
        model_version TEXT NOT NULL CHECK(length(trim(model_version)) > 0),
        predicted_at TEXT NOT NULL)""")
    timestamp = utc_timestamp()
    for row in conn.execute("""SELECT f.*, p.predicted_at FROM feedback_records f
                              LEFT JOIN predictions p ON p.feedback_id=f.id""").fetchall():
        received_at = normalized_time(row["predicted_at"]) if row["predicted_at"] else timestamp
        conn.execute("INSERT INTO feedback_records_v2 VALUES (?,?,?,?,?,?)",
                     (row["id"], row["text"], row["text"], row["source"], row["created_at"], received_at))
    for row in conn.execute("SELECT * FROM predictions").fetchall():
        conn.execute("INSERT INTO predictions_v2 VALUES (?,?,?,?,?,?,?,?)", (
            row["id"], row["feedback_id"], row["sentiment_label"], row["sentiment_confidence"],
            row["topic_label"], row["topic_confidence"], row["model_version"],
            normalized_time(row["predicted_at"]),
        ))
    conn.execute("DROP TABLE predictions")
    conn.execute("DROP TABLE feedback_records")
    conn.execute("ALTER TABLE feedback_records_v2 RENAME TO feedback_records")
    conn.execute("ALTER TABLE predictions_v2 RENAME TO predictions")
    for name in ("feedback_records", "predictions"):
        if name in sequences:
            conn.execute("UPDATE sqlite_sequence SET seq=max(seq,?) WHERE name=?", (sequences[name], name))
    for name, columns in (
        ("idx_predictions_sentiment", "sentiment_label, predicted_at, feedback_id"),
        ("idx_predictions_topic", "topic_label, predicted_at, feedback_id"),
        ("idx_predictions_time", "predicted_at, feedback_id"),
    ):
        conn.execute(f"CREATE INDEX {name} ON predictions({columns})")


MIGRATIONS = ((1, "initial", initial), (2, "feedback_metadata", feedback_metadata))


def migrate(conn: sqlite3.Connection) -> None:
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)""")
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    if applied - {version for version, _, _ in MIGRATIONS}:
        raise RuntimeError("Database schema is newer than this application")
    for version, name, operation in MIGRATIONS:
        if version not in applied:
            operation(conn)
            conn.execute("INSERT INTO schema_migrations VALUES (?,?,?)", (version, name, utc_timestamp()))
    if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise RuntimeError("Database contains an invalid foreign-key reference")
