"""Predictor adapter for trusted, checksum-verified imported PhoBERT runs."""
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from threading import Lock

from .labels import SENTIMENT_LABELS, TOPIC_LABELS
from .preprocessing import normalize_text


def verified_run(path: Path, task: str) -> tuple[dict, dict]:
    receipt = json.loads((path / "import.json").read_text(encoding="utf-8"))
    hashes = receipt.get("files_sha256", {})
    required = {"run.json", "best_model/config.json", "best_model/model.safetensors",
                "best_model/tokenizer_config.json", "best_model/special_tokens_map.json",
                "best_model/vocab.txt", "best_model/bpe.codes"}
    if receipt.get("status") != "complete" or not required.issubset(hashes):
        raise ValueError("Incomplete PhoBERT import receipt")
    for relative, expected in hashes.items():
        parts = PurePosixPath(relative)
        if parts.is_absolute() or ".." in parts.parts or "\\" in relative or ":" in relative:
            raise ValueError("Unsafe PhoBERT receipt path")
        with path.joinpath(*parts.parts).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
                raise ValueError("PhoBERT file integrity check failed")
    run = json.loads((path / "run.json").read_text(encoding="utf-8"))
    dataset = run.get("dataset", {})
    if (run.get("status") != "complete" or run.get("model") != "phobert"
            or run.get("task") != task or dataset.get("source") != "huggingface"
            or dataset.get("dataset_name") != "uitnlp/vietnamese_students_feedback"
            or not re.fullmatch(r"[0-9a-f]{40}", dataset.get("revision", ""))
            or not re.fullmatch(r"[0-9a-f]{40}", run.get("model_revision", ""))):
        raise ValueError("Unsupported PhoBERT provenance")
    config = json.loads((path / "best_model/config.json").read_text(encoding="utf-8"))
    labels = SENTIMENT_LABELS if task == "sentiment" else TOPIC_LABELS
    if (config.get("model_type") != "roberta"
            or config.get("id2label") != {str(k): v for k, v in labels.items()}
            or config.get("label2id") != {v: k for k, v in labels.items()}
            or run["config"]["phobert"]["max_length"] != 128):
        raise ValueError("Unsupported PhoBERT labels/preprocessing")
    expected_preprocessing = {"unicode_form": "NFC", "collapse_whitespace": True,
                              "preserve_casing": True, "strip_margins": True}
    if dataset.get("preprocessing") != expected_preprocessing:
        raise ValueError("Unsupported PhoBERT normalization")
    return run, hashes


class PhoBERTService:
    is_fallback = False

    def __init__(self, sentiment_run: Path, topic_run: Path, threads: int = 1):
        directories = {"sentiment": sentiment_run, "topic": topic_run}
        runs, hashes = {}, {}
        for task, directory in directories.items():
            runs[task], hashes[task] = verified_run(directory, task)
        if (runs["sentiment"]["dataset"] != runs["topic"]["dataset"]
                or runs["sentiment"]["config"] != runs["topic"]["config"]
                or runs["sentiment"]["model_revision"] != runs["topic"]["model_revision"]):
            raise ValueError("PhoBERT task runs do not match")
        identity = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
        self.model_version = "phobert-" + identity[:24]
        from .phobert_runtime import PhoBERTCPU
        self.runtime = PhoBERTCPU(directories, runs, threads)
        self.lock = Lock()

    def predict(self, text: str) -> dict:
        text = normalize_text(text)
        # Bound concurrent model work and PyVi access in a single worker process.
        with self.lock:
            result = self.runtime.predict(text)
        sentiment = result["sentiment"]
        topic = result["topic"]
        return {"text": text, "sentiment_label": SENTIMENT_LABELS[sentiment["label_id"]],
                "sentiment_confidence": max(sentiment["probabilities"]),
                "topic_label": TOPIC_LABELS[topic["label_id"]],
                "topic_confidence": max(topic["probabilities"]), "model_version": self.model_version}
