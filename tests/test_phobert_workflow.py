"""Synthetic archive safety/regression fixtures; never evidence of model quality."""
import importlib
import json
import zipfile
from types import SimpleNamespace

import pytest

from backend.app.labels import SENTIMENT_LABELS
from ml.deployment.import_phobert import check_import, import_run
from ml.evaluation.metrics import build_task_metrics


@pytest.fixture
def exported(tmp_path, monkeypatch):
    module = importlib.import_module("ml.deployment.import_phobert")
    data = {split: [{"sentence": "fixture", "sentiment": 0, "topic": 0}]
            for split in ("train", "validation", "test")}
    manifest = {"source": "test-fixture"}
    monkeypatch.setattr(module, "load_prepared", lambda path: (data, manifest))
    root = "phobert-sentiment-fixture"
    run = {"model": "phobert", "status": "complete", "task": "sentiment",
           "dataset": manifest, "model_revision": "a" * 40,
           "config": {"phobert": {"max_length": 128}}}
    metrics = {**run, **{split: {"sentiment": build_task_metrics([0], [0], "sentiment")}
                        for split in ("validation", "test")}}
    config = {"model_type": "roberta", "id2label": {str(k): v for k, v in SENTIMENT_LABELS.items()},
              "label2id": {v: k for k, v in SENTIMENT_LABELS.items()}}
    files = {"run.json": json.dumps(run), "metrics.json": json.dumps(metrics),
             "predictions.json": json.dumps({"validation": [0], "test": [0]}),
             "best_model/config.json": json.dumps(config),
             **{f"best_model/{name}": "test data" for name in (
                 "model.safetensors", "vocab.txt", "bpe.codes", "tokenizer_config.json",
                 "special_tokens_map.json", "training_args.bin")}}

    def archive(extra=None):
        path = tmp_path / f"results-{len(list(tmp_path.glob('*.zip')))}.zip"
        with zipfile.ZipFile(path, "w") as output:
            for name, body in {**files, **(extra or {})}.items():
                output.writestr(f"{root}/{name}", body)
        return path

    return SimpleNamespace(data=data, manifest=manifest, archive=archive, files=files, root=root)


def test_import_preserves_source_excludes_pickle_and_checks_tampering(tmp_path, exported):
    source = exported.archive()
    original = source.read_bytes()
    path = import_run(source, tmp_path, tmp_path / "runs")
    assert source.read_bytes() == original
    assert not (path / "best_model/training_args.bin").exists()
    assert check_import(path, exported.manifest, exported.data)[0]["task"] == "sentiment"
    with pytest.raises(FileExistsError):
        import_run(source, tmp_path, tmp_path / "runs")
    (path / "best_model/model.safetensors").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        check_import(path, exported.manifest, exported.data)


@pytest.mark.parametrize("bad_name", ["../../escape.txt", "C:/escape.txt", "..\\escape.txt"])
def test_import_rejects_unsafe_archive_before_writing(tmp_path, exported, bad_name):
    with pytest.raises(ValueError, match="Unsafe"):
        import_run(exported.archive({bad_name: "bad"}), tmp_path, tmp_path / "runs")
    assert not (tmp_path / "runs").exists()


def test_import_rejects_inconsistent_metrics_before_writing(tmp_path, exported):
    metrics = json.loads(exported.files["metrics.json"])
    metrics["test"]["sentiment"]["accuracy"] = 0
    with pytest.raises(ValueError, match="metrics"):
        import_run(exported.archive({"metrics.json": json.dumps(metrics)}), tmp_path, tmp_path / "runs")
    assert not (tmp_path / "runs").exists()


def test_reload_comparison_records_mismatches_without_claiming_full_evaluation(tmp_path, monkeypatch):
    module = importlib.import_module("ml.evaluation.phobert")
    import sys
    data = {"validation": [{"sentence": "fixture"}], "test": []}
    manifest = {"revision": "fixture", "sha256": {}}
    monkeypatch.setattr(module, "load_prepared", lambda path: (data, manifest))
    for task in ("sentiment", "topic"):
        path = tmp_path / task
        (path / "best_model").mkdir(parents=True)
        (path / "best_model/model.safetensors").write_bytes(b"fixture")
        (path / "predictions.json").write_text(json.dumps({"validation": [0]}))
    monkeypatch.setattr(module, "check_import", lambda path, *args: (
        {"task": path.name, "model_revision": "a" * 40, "config": {}}, {}))
    monkeypatch.setattr(module, "PhoBERTCPU", lambda *args: SimpleNamespace(
        predict=lambda text: {"sentiment": {"label_id": 1}, "topic": {"label_id": 0}}))
    monkeypatch.setitem(sys.modules, "psutil", SimpleNamespace(
        Process=lambda: SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=1)),
        virtual_memory=lambda: SimpleNamespace(total=1)))
    output = tmp_path / "reload.json"
    with pytest.raises(ValueError, match="differ"):
        module.evaluate_cpu(tmp_path, tmp_path / "sentiment", tmp_path / "topic", output, samples=1)
    report = json.loads(output.read_text())
    assert report["status"] == "failed"
    assert report["checked_samples"] == 1
    assert report["mismatched_indices"] == {"sentiment": [0], "topic": []}
    assert "not full evaluation" in report["sample_selection"]
