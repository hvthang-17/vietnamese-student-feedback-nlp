"""SQLite implementation of FeedbackStore. SQL stays outside application services."""
from .database import Database
from .domain.models import FeedbackFilter, FeedbackWrite, utc_timestamp
from .labels import SENTIMENT_LABELS, TOPIC_LABELS

SELECT = """SELECT f.id, f.raw_text, f.text, f.source, f.created_at, f.received_at,
    p.sentiment_label, p.sentiment_confidence, p.topic_label, p.topic_confidence,
    p.model_version, p.predicted_at
    FROM feedback_records f JOIN predictions p ON p.feedback_id=f.id"""
JOIN = "FROM feedback_records f JOIN predictions p ON p.feedback_id=f.id"


def where(filters: FeedbackFilter) -> tuple[str, list]:
    clauses, params = [], []
    for name, value in (("sentiment_label", filters.sentiment), ("topic_label", filters.topic)):
        if value:
            clauses.append(f"p.{name} = ?")
            params.append(str(value))
    for operator, value in ((">=", filters.predicted_from), ("<", filters.predicted_to)):
        if value is not None:
            clauses.append(f"p.predicted_at {operator} ?")
            params.append(utc_timestamp(value))
    return (" WHERE " + " AND ".join(clauses) if clauses else ""), params


class SQLiteFeedbackRepository:
    def __init__(self, database: Database):
        self.database = database

    def save_many(self, records: list[FeedbackWrite]) -> list[dict]:
        results = []
        with self.database.transaction(write=True) as conn:
            for item in records:
                prediction = item.prediction.to_dict()
                cursor = conn.execute("""INSERT INTO feedback_records
                    (raw_text,text,source,created_at,received_at) VALUES (?,?,?,?,?)""",
                    (item.raw_text, prediction["text"], str(item.source), item.created_at, item.received_at))
                feedback_id = cursor.lastrowid
                conn.execute("""INSERT INTO predictions
                    (feedback_id,sentiment_label,sentiment_confidence,topic_label,
                     topic_confidence,model_version,predicted_at) VALUES (?,?,?,?,?,?,?)""",
                    (feedback_id, prediction["sentiment_label"], prediction["sentiment_confidence"],
                     prediction["topic_label"], prediction["topic_confidence"],
                     prediction["model_version"], item.predicted_at))
                results.append({"feedback_id": feedback_id, "raw_text": item.raw_text,
                                **prediction, "predicted_at": item.predicted_at})
        return results

    def get(self, feedback_id: int) -> dict | None:
        with self.database.connection() as conn:
            row = conn.execute(SELECT + " WHERE f.id=?", (feedback_id,)).fetchone()
        return dict(row) if row else None

    def list_page(self, filters: FeedbackFilter, page: int, page_size: int) -> dict:
        conditions, params = where(filters)
        with self.database.transaction() as conn:
            total = conn.execute("SELECT count(*) " + JOIN + conditions, params).fetchone()[0]
            rows = conn.execute(SELECT + conditions + " ORDER BY f.id DESC LIMIT ? OFFSET ?",
                                [*params, page_size, (page - 1) * page_size]).fetchall()
        return {"items": [dict(row) for row in rows], "total": total,
                "page": page, "page_size": page_size}

    def summary(self, filters: FeedbackFilter) -> dict:
        conditions, params = where(filters)
        sentiments = {label: 0 for label in SENTIMENT_LABELS.values()}
        topics = {label: 0 for label in TOPIC_LABELS.values()}
        matrix = {topic: dict.fromkeys(sentiments, 0) for topic in topics}
        with self.database.transaction() as conn:
            groups = conn.execute("""SELECT p.sentiment_label, p.topic_label, count(*) AS n """
                                  + JOIN + conditions + " GROUP BY p.sentiment_label, p.topic_label", params)
            for row in groups:
                sentiments[row["sentiment_label"]] += row["n"]
                topics[row["topic_label"]] += row["n"]
                matrix[row["topic_label"]][row["sentiment_label"]] += row["n"]
            dated = conn.execute("SELECT count(f.created_at) " + JOIN + conditions, params).fetchone()[0]
        return {"total": sum(sentiments.values()), "sentiment": sentiments, "topic": topics,
                "matrix": matrix, "has_timestamps": bool(dated)}

    def export_rows(self, filters: FeedbackFilter, limit: int) -> list[dict]:
        conditions, params = where(filters)
        with self.database.connection() as conn:
            rows = conn.execute(SELECT + conditions + " ORDER BY f.id DESC LIMIT ?", [*params, limit]).fetchall()
        return [dict(row) for row in rows]
