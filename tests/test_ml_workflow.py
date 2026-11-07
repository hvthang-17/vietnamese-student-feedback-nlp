"""Offline regression tests. Fixtures are tiny test data, never benchmark evidence."""
import hashlib
import json
import subprocess
import sys
from types import SimpleNamespace
from dataclasses import replace

import pytest

from ml.core.config import get_config
from ml.core.runs import create_run, write_json
from ml.data import dataset
from ml.data.eda import describe
from ml.deployment.promote import check_eligibility
from ml.evaluation.metrics import benchmark_cpu_latency, build_task_metrics, create_standard_metrics_report


@pytest.fixture
def snapshot(tmp_path, monkeypatch):
    cfg = replace(get_config(), split_counts={"train": 3, "validation": 3, "test": 3, "total": 9})
    monkeypatch.setattr(dataset, "get_config", lambda: cfg)
    data = {split: [
        {"sentence": f"{split} sample {i}", "sentiment": i, "topic": i} for i in range(3)
    ] for split in dataset.SPLITS}
    hashes = {}
    for split, rows in data.items():
        path = tmp_path / f"{split}.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        hashes[split] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {"schema_version": 1, "source": "huggingface",
                "dataset_name": cfg.dataset_name, "revision": "0" * 40,
                "preprocessing": cfg.to_dict()["preprocessing"],
                "sha256": hashes, "validation": dataset.validate_splits(data)}
    write_json(tmp_path / "manifest.json", manifest)
    return tmp_path


def test_snapshot_tampering_is_rejected(snapshot):
    dataset.load_prepared(snapshot)
    (snapshot / "test.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        dataset.load_prepared(snapshot)


def test_synthetic_source_is_rejected(snapshot):
    manifest = json.loads((snapshot / "manifest.json").read_text())
    manifest["source"] = "canonical_local_seed"
    write_json(snapshot / "manifest.json", manifest)
    with pytest.raises(ValueError, match="official"):
        dataset.load_prepared(snapshot)


@pytest.mark.parametrize("field,value", [("sentence", " "), ("sentiment", 3), ("topic", -1), ("sentiment", True)])
def test_invalid_rows_are_rejected(field, value):
    row = {"sentence": "valid", "sentiment": 0, "topic": 0, field: value}
    with pytest.raises(ValueError):
        dataset.validate_splits({split: [row] for split in dataset.SPLITS})


def test_overlap_is_reported_without_repartitioning():
    row = {"sentence": "shared", "sentiment": 0, "topic": 0}
    data = {split: [row, dict(row)] for split in dataset.SPLITS}
    result = dataset.validate_splits(data)
    assert result["train"]["duplicate_rows"] == 1
    assert result["overlap_unique_texts"]["train:test"] == 1
    assert len(data["train"]) == 2


def test_download_failure_does_not_create_fallback(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("offline")
    monkeypatch.setitem(sys.modules, "datasets", SimpleNamespace(load_dataset=fail))
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(
        HfApi=lambda: SimpleNamespace(dataset_info=lambda *a, **kw: SimpleNamespace(sha="pinned"))))
    destination = tmp_path / "snapshot"
    with pytest.raises(RuntimeError, match="offline"):
        dataset.prepare(destination, "refs/convert/parquet")
    assert not destination.exists()


def test_expected_split_counts_are_enforced():
    row = {"sentence": "sample", "sentiment": 0, "topic": 0}
    with pytest.raises(ValueError, match="count"):
        dataset.validate_splits({s: [row] for s in dataset.SPLITS}, {s: 2 for s in dataset.SPLITS})


def test_measured_eda_and_no_overwrite(snapshot):
    output = snapshot / "eda.json"
    describe(snapshot, output)
    report = json.loads(output.read_text())
    assert sum(map(sum, report["splits"]["train"]["topic_sentiment_matrix"])) == 3
    with pytest.raises(FileExistsError):
        describe(snapshot, output)


def test_run_directory_is_never_reused(tmp_path):
    path = tmp_path / "run"
    create_run(path, "baseline", {}, {})
    with pytest.raises(FileExistsError):
        create_run(path, "baseline", {}, {})


def test_missing_latency_cannot_pass_acceptance():
    report = create_standard_metrics_report(
        "test", "v1", [0, 1, 2], [0, 1, 2], [0, 1, 2, 3], [0, 1, 2, 3],
        [0, 1, 2], [0, 1, 2], [0, 1, 2, 3], [0, 1, 2, 3], {},
    )
    assert report["acceptance_verification"]["latency_target_met"] is False
    assert report["acceptance_verification"]["all_criteria_met"] is False


def test_fixed_class_macro_f1_and_empty_benchmark():
    # Only class 0 appears: absent classes still contribute zero to macro F1.
    assert build_task_metrics([0, 0], [0, 0], "sentiment")["macro_f1"] == 0.3333
    with pytest.raises(ValueError):
        benchmark_cpu_latency(lambda text: text, [])


def test_promotion_rejects_missing_measurement_and_modified_artifact(tmp_path, monkeypatch):
    artifact = tmp_path / "model.joblib"
    artifact.write_bytes(b"not loaded by eligibility checks")
    checksum = hashlib.sha256(artifact.read_bytes()).hexdigest()
    write_json(tmp_path / "metrics.json", {"model_version": "v1", "test": {
        "sentiment": {"macro_f1": 0.9}, "topic": {"macro_f1": 0.8}}})
    write_json(tmp_path / "run.json", {
        "status": "complete", "model": "baseline", "model_version": "v1",
        "artifact_sha256": checksum,
        "metrics_sha256": hashlib.sha256((tmp_path / "metrics.json").read_bytes()).hexdigest(),
        "dataset": {"source": "huggingface", "revision": "test", "sha256": {}},
    })
    benchmark = tmp_path / "benchmark.json"
    report = {"model_version": "v1", "artifact_sha256": checksum,
              "dataset_revision": "test", "dataset_sha256": {},
              "benchmarks": {"measured_samples": 10}}
    write_json(benchmark, report)
    with pytest.raises(ValueError, match="latency"):
        check_eligibility(tmp_path, benchmark)
    report["benchmarks"]["p95_cpu_latency_ms"] = 1
    write_json(benchmark, report)
    assert check_eligibility(tmp_path, benchmark) == artifact
    from ml.deployment import promote as promotion
    monkeypatch.setattr(promotion, "ROOT_DIR", tmp_path / "isolated-api")
    promotion.promote(tmp_path, benchmark)
    target = tmp_path / "isolated-api/artifacts/production.joblib"
    assert target.read_bytes() == artifact.read_bytes()
    with pytest.raises(FileExistsError):
        promotion.promote(tmp_path, benchmark)
    promotion.promote(tmp_path, benchmark, replace=True)
    artifact.write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksums"):
        check_eligibility(tmp_path, benchmark)


@pytest.mark.parametrize("command", [[], ["prepare"], ["eda"], ["train-baseline"],
                                      ["train-phobert"], ["benchmark"], ["promote"],
                                      ["import-phobert"], ["verify-phobert"], ["benchmark-phobert"]])
def test_stage_help_needs_no_ml_runtime(command):
    result = subprocess.run([sys.executable, "-B", "-m", "ml", *command, "--help"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_baseline_run_and_benchmark_on_toy_fixture(tmp_path, monkeypatch):
    """Exercise the real estimator/serialization path, not a UIT-VSFC experiment."""
    import importlib
    from ml.training import baseline
    benchmark_module = importlib.import_module("ml.evaluation.benchmark")
    rows = [{"sentence": f"sentiment{s} topic{t} feedback example", "sentiment": s, "topic": t}
            for _ in range(4) for s in range(3) for t in range(4)]
    data = {split: rows for split in dataset.SPLITS}
    manifest = {"source": "test-fixture", "revision": "toy", "sha256": {}}
    monkeypatch.setattr(baseline, "load_prepared", lambda path: (data, manifest))
    monkeypatch.setattr(benchmark_module, "load_prepared", lambda path: (data, manifest))
    run_dir = tmp_path / "baseline-smoke"
    baseline.train(tmp_path, run_dir)
    assert json.loads((run_dir / "run.json").read_text())["status"] == "complete"
    # Check the existing backend interface without touching its real artifact/database.
    import shutil
    from backend.app import inference
    serving = tmp_path / "serving"
    serving.mkdir()
    shutil.copyfile(run_dir / "model.joblib", serving / "production.joblib")
    monkeypatch.setattr(inference, "ARTIFACTS", serving)
    service = inference.InferenceService()
    result = service.predict(rows[0]["sentence"])
    assert not service.is_fallback
    assert result["sentiment_label"] in {"negative", "neutral", "positive"}
    assert 0 <= result["topic_confidence"] <= 1
    benchmark_file = tmp_path / "benchmark.json"
    benchmark_module.benchmark(tmp_path, run_dir, benchmark_file)
    assert json.loads(benchmark_file.read_text())["benchmarks"]["measured_samples"] == len(rows)
    with pytest.raises(ValueError, match="Official"):
        check_eligibility(run_dir, benchmark_file)


def test_metrics_match_sklearn_reference():
    from sklearn.metrics import accuracy_score, f1_score
    truth, predicted = [0, 0, 0, 1, 1, 2, 3, 3], [0, 1, 0, 1, 2, 2, 0, 3]
    metrics = build_task_metrics(truth, predicted, "topic")
    assert metrics["accuracy"] == round(accuracy_score(truth, predicted), 4)
    for average in ("macro", "weighted"):
        assert metrics[f"{average}_f1"] == round(f1_score(
            truth, predicted, labels=[0, 1, 2, 3], average=average, zero_division=0), 4)
