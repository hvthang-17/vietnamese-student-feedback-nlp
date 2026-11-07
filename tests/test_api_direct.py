"""Application/repository tests independent of HTTP and real artifacts."""
import sqlite3
from datetime import datetime, timezone
import pytest
from backend.app.domain.models import FeedbackFilter, Source
from backend.app.services.imports import ImportService
from backend.app.settings import Settings


def test_single_prediction_flow(service, repository):
    result = service.predict("  Giảng viên   hay ")
    assert result["raw_text"] == "  Giảng viên   hay "
    assert result["text"] == "Giảng viên hay"
    assert repository.get(result["feedback_id"])["source"] == "manual"


def test_batch_order_and_database_rollback(service, repository):
    result = service.predict_many([("first", None), ("second", None)], Source.BATCH)
    assert [r["text"] for r in result] == ["first", "second"]
    # A DB constraint failure on item 2 rolls back item 1 as well.
    with repository.database.connection() as conn:
        conn.execute("""CREATE TRIGGER reject_bad BEFORE INSERT ON feedback_records
                        WHEN NEW.text='bad' BEGIN SELECT RAISE(ABORT,'test failure'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        service.predict_many([("third", None), ("bad", None)], Source.BATCH)
    assert repository.list_page(FeedbackFilter(), 1, 20)["total"] == 2


def test_import_validation_precedes_persistence(service, repository, settings):
    result = ImportService(service, settings).import_csv(b'text\n""\nvalid\n')
    assert result["imported"] == 1
    assert result["errors"][0]["row"] == 2
    assert repository.summary(FeedbackFilter())["total"] == 1


def test_created_at_and_raw_text_are_distinct(service, repository):
    created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = service.predict("  feedback  ", created)
    row = repository.get(result["feedback_id"])
    assert row["created_at"].startswith("2026-01-01")
    assert row["raw_text"] == "  feedback  "
    assert row["text"] == "feedback"
    assert row["received_at"] <= row["predicted_at"]


def test_foreign_keys_are_enforced(repository):
    with repository.database.connection() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""INSERT INTO predictions (feedback_id,sentiment_label,sentiment_confidence,
                         topic_label,topic_confidence,model_version,predicted_at)
                         VALUES (999,'positive',0.8,'lecturer',0.9,'v1','date')""")
