"""Benchmark the exact baseline artifact on matching prepared test inputs."""
import hashlib
import json
from pathlib import Path
from backend.app.preprocessing import normalize_text
from ml.core.runs import environment, write_json
from ml.data.dataset import load_prepared


def benchmark(data_dir: Path, run_dir: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    import joblib
    from ml.evaluation.metrics import benchmark_cpu_latency

    data, manifest = load_prepared(data_dir)
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    if run.get("status") != "complete" or run.get("model") != "baseline":
        raise ValueError("Benchmark currently supports a completed baseline run only.")
    if run["dataset"] != manifest:
        raise ValueError("Benchmark must use the same dataset snapshot as training.")
    path = run_dir / "model.joblib"
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    if checksum != run["artifact_sha256"]:
        raise ValueError("Run artifact checksum mismatch.")
    bundle = joblib.load(path)

    def predict(text):
        text = normalize_text(text)
        return (bundle["sentiment_model"].predict_proba([text]),
                bundle["topic_model"].predict_proba([text]))

    report = {
        "model_version": run["model_version"], "artifact_sha256": checksum,
        "dataset_sha256": manifest["sha256"], "dataset_revision": manifest["revision"],
        "scope": "normalize + joint predict_proba; CPU; batch=1; excludes database/HTTP/load",
        "environment": environment(),
        "benchmarks": benchmark_cpu_latency(predict, [r["sentence"] for r in data["test"][:300]]),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)
    print(f"CPU benchmark: {output}; p95={report['benchmarks']['p95_cpu_latency_ms']} ms")
