"""Opt-in real loopback HTTP/SQLite integration and latency measurement."""
import argparse
import json
import socket
import tempfile
import threading
import time
from pathlib import Path
from statistics import mean

from ml.core.runs import environment, write_json
from ml.data.dataset import load_prepared
from ml.evaluation.metrics import percentile


def measure(data_dir: Path, sentiment_run: Path, topic_run: Path, output: Path, samples: int):
    if output.exists():
        raise FileExistsError(output)
    data, manifest = load_prepared(data_dir)
    if not 1 <= samples <= len(data["test"]):
        raise ValueError("Invalid sample count")
    import httpx
    import uvicorn
    from backend.app.main import create_app
    from backend.app.settings import Settings
    with tempfile.TemporaryDirectory(prefix="vsfc-http-") as temporary:
        settings = Settings(environment="test", database_path=Path(temporary) / "test.db",
                            model_backend="phobert", phobert_sentiment_run=sentiment_run,
                            phobert_topic_run=topic_run, allow_demo_model=False, log_level="error")
        app = create_app(settings)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
            server = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False))
            thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
            thread.start()
            try:
                deadline = time.monotonic() + 180
                while not server.started:
                    if not thread.is_alive() or time.monotonic() > deadline:
                        raise RuntimeError("API startup failed or timed out")
                    time.sleep(0.05)
                with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=120, trust_env=False) as client:
                    def post(text):
                        response = client.post("/api/v1/predictions", json={"text": text})
                        response.raise_for_status()
                        return response.json()

                    health = client.get("/health").json()
                    assert not health["fallback_model"] and health["model_version"].startswith("phobert-")
                    assert client.get("/ready").status_code == 200
                    raw = "  Giảng viên rất nhiệt tình.  "
                    prediction = post(raw)
                    saved = client.get(f"/api/v1/feedback/{prediction['feedback_id']}").json()
                    assert saved["raw_text"] == raw and saved["text"] == raw.strip()
                    items = [{"text": row["sentence"]} for row in data["validation"][:3]]
                    batch = client.post("/api/v1/predictions/batch", json={"items": items})
                    batch.raise_for_status()
                    assert [r["text"] for r in batch.json()] == [r["text"] for r in items]
                    csv = client.post("/api/v1/imports/csv", files={"file": (
                        "test.csv", "text\nGiảng viên tốt\n\"\"\nPhòng học tốt\n".encode(), "text/csv")})
                    csv.raise_for_status()
                    assert csv.json()["imported"] == 2 and len(csv.json()["errors"]) == 1
                    assert client.post("/api/v1/predictions", json={"text": " "}).status_code == 422
                    predictor = app.state.feedback.predictor
                    original = predictor.runtime.predict
                    total = client.get("/api/v1/feedback").json()["total"]
                    calls = 0

                    def fail_second(text):
                        nonlocal calls
                        calls += 1
                        if calls == 2:
                            raise RuntimeError("injected integration failure")
                        return original(text)

                    predictor.runtime.predict = fail_second
                    try:
                        failed = client.post("/api/v1/predictions/batch", json={"items": items})
                        assert failed.status_code == 500 and "injected" not in failed.text
                        assert client.get("/api/v1/feedback").json()["total"] == total
                    finally:
                        predictor.runtime.predict = original
                    long_started = time.perf_counter()
                    post(("giảng viên tốt " * 400)[:5000])
                    long_ms = (time.perf_counter() - long_started) * 1000
                    for row in data["test"][:5]:
                        post(row["sentence"])
                    times = []
                    for index, row in enumerate(data["test"][:samples]):
                        started = time.perf_counter()
                        result = post(row["sentence"])
                        times.append((time.perf_counter() - started) * 1000)
                        assert result["model_version"] == health["model_version"]
                        if (index + 1) % 50 == 0:
                            print(f"HTTP benchmark {index + 1}/{samples}", flush=True)
                    assert client.get("/api/v1/feedback").json()["total"] == total + 1 + 5 + samples
                    report = {"status": "passed", "environment": environment(),
                              "model_version": health["model_version"], "dataset_sha256": manifest["sha256"],
                              "scope": "loopback TCP HTTP + validation + joint inference + SQLite commit; one client, no concurrency; excludes startup",
                              "samples": samples, "warmups": 5, "cpu_threads": 1,
                              "mean_ms": round(mean(times), 2), "p95_ms": round(percentile(times, .95), 2),
                              "max_ms": round(max(times), 2), "single_5000_char_ms": round(long_ms, 2),
                              "integration": ["health/ready", "single persisted raw/normalized text", "batch order",
                                              "CSV partial input rejection", "422 validation", "inference failure atomicity/redaction"],
                              "database": "temporary; deleted after run", "production_changed": False}
                    report["p95_target_met"] = report["p95_ms"] < 2000
                    output.parent.mkdir(parents=True, exist_ok=True)
                    write_json(output, report)
                    print(f"HTTP p95={report['p95_ms']} ms; report={output}", flush=True)
            finally:
                server.should_exit = True
                thread.join(timeout=30)
                if thread.is_alive():
                    raise RuntimeError("API shutdown did not complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--sentiment-run", type=Path, required=True)
    parser.add_argument("--topic-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=300)
    args = parser.parse_args()
    measure(args.data_dir, args.sentiment_run, args.topic_run, args.output, args.samples)
