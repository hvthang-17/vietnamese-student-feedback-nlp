"""Adapter contract and fail-closed checks without heavyweight dependencies."""
import hashlib
import json

import pytest

from backend.app.labels import SENTIMENT_LABELS, TOPIC_LABELS
from backend.app.phobert import PhoBERTService
from backend.app.settings import Settings


@pytest.fixture
def runs(tmp_path, monkeypatch):
    from backend.app import phobert_runtime
    class Runtime:
        def __init__(self, *args):
            pass

        def predict(self, text):
            return {"sentiment": {"label_id": 2, "probabilities": [0.1, 0.1, 0.8]},
                    "topic": {"label_id": 0, "probabilities": [0.7, 0.1, 0.1, 0.1]}}

    monkeypatch.setattr(phobert_runtime, "PhoBERTCPU", Runtime)
    paths = []
    for task, labels in (("sentiment", SENTIMENT_LABELS), ("topic", TOPIC_LABELS)):
        path = tmp_path / task
        (path / "best_model").mkdir(parents=True)
        run = {"status": "complete", "model": "phobert", "task": task,
               "model_revision": "a" * 40, "config": {"phobert": {"max_length": 128}},
               "dataset": {"source": "huggingface", "revision": "b" * 40,
                           "dataset_name": "uitnlp/vietnamese_students_feedback",
                           "preprocessing": {"unicode_form": "NFC", "collapse_whitespace": True,
                                             "preserve_casing": True, "strip_margins": True}}}
        files = {"run.json": json.dumps(run), "best_model/config.json": json.dumps({
            "model_type": "roberta", "id2label": labels,
            "label2id": {v: k for k, v in labels.items()}})}
        for name in ("model.safetensors", "tokenizer_config.json", "special_tokens_map.json", "vocab.txt", "bpe.codes"):
            files["best_model/" + name] = "fixture only, no real model"
        hashes = {}
        for rel, body in files.items():
            (path / rel).write_text(body, encoding="utf-8")
            hashes[rel] = hashlib.sha256((path / rel).read_bytes()).hexdigest()
        (path / "import.json").write_text(json.dumps({"status": "complete", "files_sha256": hashes}))
        paths.append(path)
    return paths


def test_adapter_contract_and_integrity(runs):
    service = PhoBERTService(*runs)
    result = service.predict("  Nội dung   tốt ")
    assert result["text"] == "Nội dung tốt"
    assert result["sentiment_label"] == "positive" and result["topic_label"] == "lecturer"
    assert result["sentiment_confidence"] == 0.8 and not service.is_fallback
    assert result["model_version"].startswith("phobert-")
    (runs[0] / "best_model/model.safetensors").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="integrity"):
        PhoBERTService(*runs)


def test_settings_explicit_selection(monkeypatch, runs):
    with pytest.raises(ValueError, match="both task"):
        Settings(model_backend="phobert")
    with pytest.raises(ValueError, match="MODEL_BACKEND"):
        Settings(model_backend="unknown")
    monkeypatch.setenv("MODEL_BACKEND", "phobert")
    monkeypatch.setenv("PHOBERT_SENTIMENT_RUN", str(runs[0]))
    monkeypatch.setenv("PHOBERT_TOPIC_RUN", str(runs[1]))
    settings = Settings.from_env()
    assert settings.phobert_sentiment_run == runs[0]
    assert settings.model_backend == "phobert"
