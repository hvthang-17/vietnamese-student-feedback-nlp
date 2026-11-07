"""The only ML stage allowed to replace the backend's production model."""
import hashlib
import json
import math
import os
import shutil
from pathlib import Path
from ml.core.config import ROOT_DIR, get_config


def check_eligibility(run_dir: Path, benchmark_file: Path) -> Path:
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    benchmark = json.loads(benchmark_file.read_text(encoding="utf-8"))
    if run.get("status") != "complete" or run.get("model") != "baseline":
        raise ValueError("Only completed baseline runs are supported by the API.")
    if run.get("dataset", {}).get("source") != "huggingface":
        raise ValueError("Official dataset provenance is required.")
    if hashlib.sha256((run_dir / "metrics.json").read_bytes()).hexdigest() != run.get("metrics_sha256"):
        raise ValueError("Metrics checksum mismatch.")
    path = run_dir / "model.joblib"
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    if checksum != run.get("artifact_sha256") or checksum != benchmark.get("artifact_sha256"):
        raise ValueError("Model and benchmark artifact checksums must match.")
    if (benchmark.get("dataset_sha256") != run["dataset"]["sha256"]
            or benchmark.get("dataset_revision") != run["dataset"]["revision"]):
        raise ValueError("Benchmark dataset does not match the run.")
    if (metrics.get("model_version") != run.get("model_version")
            or benchmark.get("model_version") != run.get("model_version")):
        raise ValueError("Model versions must match.")
    cfg = get_config()
    for task, threshold in (("sentiment", cfg.target_macro_f1_sentiment),
                            ("topic", cfg.target_macro_f1_topic)):
        score = metrics.get("test", {}).get(task, {}).get("macro_f1")
        if type(score) not in (float, int) or not math.isfinite(score) or not threshold <= score <= 1:
            raise ValueError(f"{task} test target not met or missing.")
    latency = benchmark.get("benchmarks", {}).get("p95_cpu_latency_ms")
    if benchmark.get("benchmarks", {}).get("measured_samples", 0) <= 0:
        raise ValueError("A nonempty latency measurement is required.")
    if (type(latency) not in (float, int) or not math.isfinite(latency)
            or not 0 <= latency < cfg.max_p95_cpu_latency_ms):
        raise ValueError("Measured CPU latency target not met or missing.")
    return path


def promote(run_dir: Path, benchmark_file: Path, replace: bool = False) -> None:
    source = check_eligibility(run_dir, benchmark_file)
    target = ROOT_DIR / "artifacts" / "production.joblib"
    if target.exists() and not replace:
        raise FileExistsError("Production model exists. Use --replace only after reviewing this run.")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".pending")
    # Exclusive creation avoids interfering with another pending promotion.
    with temporary.open("xb") as output, source.open("rb") as model:
        shutil.copyfileobj(model, output)
    os.replace(temporary, target)
    print("Promoted baseline. Restart the API to load the new model.")
