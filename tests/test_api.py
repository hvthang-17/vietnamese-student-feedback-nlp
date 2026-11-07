"""HTTP contract tests against the real app factory and isolated SQLite."""
import csv
import io
from dataclasses import replace
from fastapi.testclient import TestClient
from backend.app.main import create_app


def test_health_and_prediction(client):
    assert client.get("/health").json()["model_version"] == "test-model-v1"
    assert client.get("/ready").status_code == 200
    text = "  Giảng viên   nhiệt tình.  "
    response = client.post("/api/v1/predictions", json={"text": text})
    assert response.status_code == 200
    assert response.headers["x-request-id"]
    body = response.json()
    assert body["raw_text"] == text
    assert body["text"] == "Giảng viên nhiệt tình."
    assert body["predicted_at"].endswith("Z") or body["predicted_at"].endswith("+00:00")
    saved = client.get(f"/api/v1/feedback/{body['feedback_id']}").json()
    assert saved["raw_text"] == text
    assert saved["source"] == "manual"


def test_validation_and_batch_order(client):
    for text in ("", "  ", "x" * 5001, "\x00invalid"):
        response = client.post("/api/v1/predictions", json={"text": text})
        assert response.status_code == 422
        assert "input" not in response.json()["detail"][0]
    response = client.post("/api/v1/predictions/batch", json={"items": [{"text": "first"}, {"text": "second"}]})
    assert response.status_code == 200
    assert [item["text"] for item in response.json()] == ["first", "second"]
    assert client.post("/api/v1/predictions/batch", json={"items": []}).status_code == 422
    assert client.post("/api/v1/predictions/batch", json={"items": [{"text": "x"}] * 101}).status_code == 422


def test_model_failure_is_redacted_and_batch_does_not_partially_commit(client):
    response = client.post("/api/v1/predictions/batch", json={"items": [
        {"text": "first"}, {"text": "MODEL_FAILURE"}]})
    assert response.status_code == 500
    assert "private" not in response.text
    assert response.headers["x-request-id"]
    assert client.get("/api/v1/feedback").json()["total"] == 0


def test_csv_first_row_error_does_not_reject_valid_later_rows(client):
    content = "text,created_at\n"",\nGiảng viên hay,2026-01-01T08:00:00+07:00\n"
    response = client.post("/api/v1/imports/csv", files={"file": ("feedback.csv", content.encode(), "text/csv")})
    assert response.status_code == 200
    assert response.json()["imported"] == 1
    assert response.json()["errors"][0]["row"] == 2
    row = client.get("/api/v1/feedback").json()["items"][0]
    assert row["source"] == "csv"
    assert row["created_at"] == "2026-01-01T01:00:00.000000+00:00"


def test_csv_bad_header_encoding_and_overlong_text(client):
    for content in (b"wrong\nvalue\n", b"text\n\xff\n", b"text,text\na,b\n", b'"unclosed header'):
        assert client.post("/api/v1/imports/csv", files={"file": ("x.csv", content)}).status_code == 422
    content = "text\n" + "x" * 5001 + "\nvalid\n"
    result = client.post("/api/v1/imports/csv", files={"file": ("x.csv", content)}).json()
    assert result["imported"] == 1
    assert len(result["errors"]) == 1


def test_csv_resource_limits_are_atomic(settings, predictor):
    app = create_app(replace(settings, max_csv_rows=1, max_csv_bytes=64), predictor)
    with TestClient(app) as client:
        for content in (b"text\nfirst\nsecond\n", b"text\n" + b"x" * 65):
            assert client.post("/api/v1/imports/csv", files={"file": ("x.csv", content)}).status_code == 413
        assert client.get("/api/v1/feedback").json()["total"] == 0
        assert client.post("/api/v1/predictions", content=b"x" * 70000,
                           headers={"Content-Type": "application/json"}).status_code == 413


def test_sql_pagination_filters_and_missing_record(client):
    client.post("/api/v1/predictions/batch", json={"items": [{"text": f"sample {i}"} for i in range(5)]})
    first = client.get("/api/v1/feedback", params={"page": 1, "page_size": 2}).json()
    second = client.get("/api/v1/feedback", params={"page": 2, "page_size": 2}).json()
    assert first["total"] == second["total"] == 5
    assert {r["id"] for r in first["items"]}.isdisjoint(r["id"] for r in second["items"])
    assert client.get("/api/v1/feedback?sentiment=negative").json()["total"] == 0
    assert client.get("/api/v1/dashboard/summary?sentiment=positive").json()["total"] == 5
    assert client.get("/api/v1/feedback/999").status_code == 404
    assert client.get("/api/v1/feedback?page_size=101").status_code == 422
    assert client.get("/api/v1/feedback?topic=unknown").status_code == 422


def test_date_filters_are_aware_and_half_open(client):
    response = client.post("/api/v1/predictions", json={"text": "dated"})
    timestamp = response.json()["predicted_at"]
    assert client.get("/api/v1/feedback", params={"predicted_from": timestamp}).json()["total"] == 1
    assert client.get("/api/v1/feedback", params={"predicted_to": timestamp}).json()["total"] == 0
    assert client.get("/api/v1/feedback", params={"predicted_from": timestamp, "predicted_to": timestamp}).status_code == 422
    assert client.get("/api/v1/feedback?predicted_from=2026-01-01T00:00:00").status_code == 422
    assert client.post("/api/v1/predictions", json={"text": "x", "created_at": "2026-01-01T00:00:00"}).status_code == 422


def test_csv_export_formula_safety_and_complete_records(client):
    client.post("/api/v1/predictions", json={"text": " =1+1"})
    response = client.get("/api/v1/exports/csv")
    assert response.status_code == 200
    assert response.content.startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert rows[0]["raw_text"] == "' =1+1"
    assert rows[0]["text"] == "'=1+1"
    assert client.get("/api/v1/exports/csv?sentiment=negative").content.decode("utf-8-sig").count("\n") == 1


def test_export_limit_is_explicit(settings, predictor):
    with TestClient(create_app(replace(settings, max_export_rows=1), predictor)) as client:
        client.post("/api/v1/predictions/batch", json={"items": [{"text": "a"}, {"text": "b"}]})
        assert client.get("/api/v1/exports/csv").status_code == 413
        assert client.get("/api/v1/exports/pdf").status_code == 413


def test_optional_authentication_cors_and_public_health(settings, predictor):
    token = "t" * 32
    app = create_app(replace(settings, api_token=token), predictor)
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/api/v1/feedback").status_code == 401
        assert client.get("/api/v1/feedback", headers={"Authorization": "Bearer wrong"}).status_code == 401
        assert client.get("/api/v1/feedback", headers={"Authorization": "Bearer " + token}).status_code == 200
        response = client.options("/api/v1/predictions", headers={
            "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_openapi_contains_versioned_contracts(client):
    schema = client.get("/openapi.json").json()
    assert "/api/v1/feedback/{feedback_id}" in schema["paths"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]
    assert "raw_text" in schema["components"]["schemas"]["PredictionResponse"]["properties"]


def test_pdf_wraps_and_includes_records_after_the_old_limit(client, monkeypatch):
    # Uncompressed streams let us verify final record inclusion without a PDF reader dependency.
    from reportlab import rl_config
    monkeypatch.setattr(rl_config, "pageCompression", 0)
    items = [{"text": f"marker-{i:03d} " + "feedback " * 80} for i in range(40)]
    assert client.post("/api/v1/predictions/batch", json={"items": items}).status_code == 200
    response = client.get("/api/v1/exports/pdf")
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    # Descending ID export: both ends must be present, not only the first 35.
    assert b"marker-000" in response.content and b"marker-039" in response.content
    assert response.content.count(b"/Type /Page") > 2


def test_unavailable_explicit_pdf_font_returns_service_error(settings, predictor, tmp_path):
    with TestClient(create_app(replace(settings, pdf_font_path=tmp_path / "missing.ttf"), predictor)) as client:
        assert client.get("/api/v1/exports/pdf").status_code == 503


def test_feedback_and_token_values_are_not_logged(client, caplog):
    import logging
    caplog.set_level(logging.INFO, logger="feedback.api")
    marker = "private-feedback-unique-marker"
    assert client.post("/api/v1/predictions", json={"text": marker}).status_code == 200
    assert "request_id=" in caplog.text
    assert marker not in caplog.text


def test_unexpected_error_does_not_escape_to_server_traceback(settings, predictor, caplog):
    with TestClient(create_app(settings, predictor), raise_server_exceptions=True) as active:
        response = active.post("/api/v1/predictions", json={"text": "MODEL_FAILURE"})
        assert response.status_code == 500
        assert "X-Request-ID" in response.headers
        assert "private model error" not in caplog.text
        assert all(record.exc_info is None for record in caplog.records)
