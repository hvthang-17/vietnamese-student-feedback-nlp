"""Classification metrics and CPU timing without heavyweight import side effects."""
import math
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from backend.app.labels import SENTIMENT_LABELS, TOPIC_LABELS
from ml.core.config import get_config
from ml.core.runs import write_json


def build_task_metrics(labels: list[int], predictions: list[int], task: str) -> dict:
    if task not in {"sentiment", "topic"}:
        raise ValueError("Unknown task: " + task)
    mapping = SENTIMENT_LABELS if task == "sentiment" else TOPIC_LABELS
    if not len(labels) or len(labels) != len(predictions):
        raise ValueError("Nonempty, equally-sized labels and predictions are required.")
    if any(type(x) is not int or x not in mapping for x in [*labels, *predictions]):
        raise ValueError("Label outside the task mapping.")
    matrix = [[0] * len(mapping) for _ in mapping]
    for truth, prediction in zip(labels, predictions):
        matrix[truth][prediction] += 1
    per_class, f1s, weighted = {}, [], 0.0
    for index, name in mapping.items():
        tp = matrix[index][index]
        support = sum(matrix[index])
        predicted = sum(row[index] for row in matrix)
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[name] = {"precision": round(precision, 4), "recall": round(recall, 4),
                           "f1_score": round(f1, 4), "support": support}
        f1s.append(f1)
        weighted += f1 * support
    return {
        "accuracy": round(sum(matrix[i][i] for i in mapping) / len(labels), 4),
        "macro_f1": round(mean(f1s), 4), "weighted_f1": round(weighted / len(labels), 4),
        "per_class": per_class, "confusion_matrix": matrix,
    }


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def benchmark_cpu_latency(predict_fn, sample_texts: list[str], warmup_runs: int = 5) -> dict:
    if not sample_texts:
        raise ValueError("Latency benchmark requires samples.")
    for text in sample_texts[:warmup_runs]:
        predict_fn(text)
    times = []
    for text in sample_texts:
        start = time.perf_counter()
        predict_fn(text)
        times.append((time.perf_counter() - start) * 1000)
    return {"mean_cpu_latency_ms": round(mean(times), 2),
            "p50_cpu_latency_ms": round(percentile(times, 0.5), 2),
            "p95_cpu_latency_ms": round(percentile(times, 0.95), 2),
            "min_cpu_latency_ms": round(min(times), 2),
            "max_cpu_latency_ms": round(max(times), 2), "measured_samples": len(times)}


def create_standard_metrics_report(
    model_name: str, model_version: str,
    val_sentiment_true, val_sentiment_pred, val_topic_true, val_topic_pred,
    test_sentiment_true, test_sentiment_pred, test_topic_true, test_topic_pred,
    benchmarks: dict, artifact_size_bytes: int = 0, extra_metadata: dict | None = None,
) -> dict:
    cfg = get_config()
    test_sent = build_task_metrics(test_sentiment_true, test_sentiment_pred, "sentiment")
    test_topic = build_task_metrics(test_topic_true, test_topic_pred, "topic")
    latency = benchmarks.get("p95_cpu_latency_ms")
    latency_met = (type(latency) in (float, int) and math.isfinite(latency)
                   and 0 <= latency < cfg.max_p95_cpu_latency_ms)
    checks = {
        "sentiment_target_met": test_sent["macro_f1"] >= cfg.target_macro_f1_sentiment,
        "topic_target_met": test_topic["macro_f1"] >= cfg.target_macro_f1_topic,
        "latency_target_met": latency_met,
    }
    return {
        "model_name": model_name, "model_version": model_version,
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": {"os": platform.system(), "os_release": platform.release(),
                        "python_version": platform.python_version(), "device": "cpu"},
        "experiment_config": cfg.to_dict(),
        "validation": {
            "sentiment": build_task_metrics(val_sentiment_true, val_sentiment_pred, "sentiment"),
            "topic": build_task_metrics(val_topic_true, val_topic_pred, "topic"),
        },
        "test": {"sentiment": test_sent, "topic": test_topic},
        "benchmarks": {**benchmarks, "artifact_size_bytes": artifact_size_bytes,
                       "artifact_size_mb": round(artifact_size_bytes / 1024**2, 2)},
        "acceptance_verification": {**checks, "all_criteria_met": all(checks.values())},
        "metadata": extra_metadata or {},
    }


def save_metrics_report(report: dict, target_path: Path | str) -> Path:
    path = Path(target_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, report)
    return path
