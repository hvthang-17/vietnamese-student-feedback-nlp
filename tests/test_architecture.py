"""Migration, domain and lifecycle regression tests using disposable databases."""
import sqlite3
import sys
from dataclasses import replace
from types import SimpleNamespace

import pytest

from backend.app.database import Database
from backend.app.domain.models import FeedbackFilter, ModelContractError
from backend.app.inference import InferenceService
from backend.app.main import create_app
from backend.app.migrations import initial
from backend.app.services.feedback import FeedbackService
from backend.app.settings import Settings


def legacy_database(path, sentiment="positive"):
    database = Database(path)
    with database.transaction(write=True) as conn:
        initial(conn)
        conn.execute("INSERT INTO feedback_records VALUES (1,'legacy feedback','csv',NULL)")
        conn.execute("INSERT INTO feedback_records VALUES (100,'deleted','manual',NULL)")
        conn.execute("DELETE FROM feedback_records WHERE id=100")
        conn.execute("""INSERT INTO predictions VALUES
            (7,1,?,0.8,'lecturer',0.9,'legacy-v1','2026-01-01T08:00:00+07:00')""", (sentiment,))
    return database


def test_legacy_migration_preserves_ids_data_and_sequence(tmp_path):
    database = legacy_database(tmp_path / "legacy.db")
    database.initialize()
    database.initialize()  # Idempotent, not destructive recreation.
    database.verify_schema()
    with database.connection() as conn:
        row = conn.execute("SELECT * FROM feedback_records").fetchone()
        assert row["id"] == 1
        assert row["text"] == row["raw_text"] == "legacy feedback"
        assert row["received_at"] == "2026-01-01T01:00:00.000000+00:00"
        prediction = conn.execute("SELECT * FROM predictions").fetchone()
        assert prediction["id"] == 7 and prediction["model_version"] == "legacy-v1"
        assert conn.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 2
        cursor = conn.execute("""INSERT INTO feedback_records (raw_text,text,source,received_at)
                                 VALUES ('new','new','manual','2026-01-01')""")
        assert cursor.lastrowid > 100
        assert conn.execute("PRAGMA foreign_key_check").fetchone() is None


def test_bad_legacy_data_aborts_entire_migration(tmp_path):
    database = legacy_database(tmp_path / "legacy.db", sentiment="invalid")
    with pytest.raises(sqlite3.IntegrityError):
        database.initialize()
    with database.connection() as conn:
        assert conn.execute("SELECT text FROM feedback_records").fetchone()[0] == "legacy feedback"
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(feedback_records)")]
        assert "raw_text" not in columns
        assert conn.execute("SELECT sentiment_label FROM predictions").fetchone()[0] == "invalid"
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='feedback_records_v2'").fetchone() is None


def test_unknown_schema_revision_is_rejected(repository):
    database = repository.database
    with database.transaction(write=True) as conn:
        conn.execute("INSERT INTO schema_migrations VALUES (99,'future','date')")
    with pytest.raises(RuntimeError, match="newer"):
        database.initialize()


def test_factory_has_no_model_or_database_io(settings, predictor):
    create_app(settings, predictor)
    assert not settings.database_path.exists()


def test_real_model_is_required_when_demo_is_disabled(tmp_path):
    with pytest.raises(FileNotFoundError):
        InferenceService(tmp_path / "absent.joblib", allow_demo=False)
    assert InferenceService(tmp_path / "absent.joblib", allow_demo=True).is_fallback


def test_production_settings_fail_closed(settings):
    with pytest.raises(ValueError, match="Production"):
        replace(settings, environment="production")
    with pytest.raises(ValueError, match="32 ASCII"):
        replace(settings, api_token="short")
    configured = replace(settings, environment="production", api_token="s" * 32,
                         allow_demo_model=False, auto_migrate=False)
    assert "s" * 32 not in repr(configured)


def test_predictor_contract_is_validated_before_database_write(repository, predictor):
    class BrokenPredictor:
        def predict(self, text):
            result = predictor.predict(text)
            result["sentiment_confidence"] = float("nan")
            return result

    service = FeedbackService(repository, BrokenPredictor())
    with pytest.raises(ModelContractError):
        service.predict("valid input")
    assert repository.summary(FeedbackFilter())["total"] == 0


def test_settings_read_environment_and_resolve_paths(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.delenv("API_TOKEN", raising=False)
    monkeypatch.setenv("DATABASE_PATH", "data/custom.db")
    monkeypatch.setenv("CORS_ORIGINS", "https://one.example, https://two.example")
    monkeypatch.setenv("MAX_CSV_ROWS", "10")
    settings = Settings.from_env()
    assert settings.database_path.is_absolute()
    assert settings.database_path.name == "custom.db"
    assert settings.cors_origins == ("https://one.example", "https://two.example")
    assert settings.max_csv_rows == 10


def test_production_loader_rejects_legacy_provenance(tmp_path, monkeypatch):
    path = tmp_path / "legacy.joblib"
    path.write_bytes(b"test artifact; deserialization replaced by a test double")
    monkeypatch.setitem(sys.modules, "joblib", SimpleNamespace(load=lambda path: {}))
    with pytest.raises(ValueError, match="provenance"):
        InferenceService(path, allow_demo=False, require_official=True)


def test_domain_enums_match_ml_and_backend_label_mappings():
    from backend.app.domain.models import Sentiment, Topic
    from backend.app.labels import SENTIMENT_LABELS, TOPIC_LABELS
    assert list(Sentiment) == list(SENTIMENT_LABELS.values())
    assert list(Topic) == list(TOPIC_LABELS.values())
