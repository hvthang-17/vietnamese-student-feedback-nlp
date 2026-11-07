"""Offline CPU reload verification and joint inference benchmark; no API promotion."""
import json
import os
import platform
import time
from pathlib import Path

from backend.app.phobert_runtime import PhoBERTCPU
from ml.core.runs import environment, write_json
from ml.data.dataset import load_prepared
from ml.deployment.import_phobert import check_import
from ml.evaluation.metrics import benchmark_cpu_latency



def evaluate_cpu(data_dir: Path, sentiment_run: Path, topic_run: Path, output: Path,
                 samples: int = 64, threads: int = 1, benchmark: bool = False) -> None:
    if output.exists():
        raise FileExistsError(output)
    if not 1 <= samples <= 3166 or not 1 <= threads <= (os.cpu_count() or 1):
        raise ValueError("Invalid samples or CPU thread count.")
    data, manifest = load_prepared(data_dir)
    if samples > len(data["test" if benchmark else "validation"]):
        raise ValueError("Sample count exceeds the selected split.")
    run_dirs = {"sentiment": sentiment_run, "topic": topic_run}
    runs, hashes = {}, {}
    for task, path in run_dirs.items():
        runs[task], hashes[task] = check_import(path, manifest, data)
        if runs[task]["task"] != task:
            raise ValueError("Sentiment/topic run arguments are swapped.")
    if (runs["sentiment"]["model_revision"] != runs["topic"]["model_revision"]
            or runs["sentiment"]["config"] != runs["topic"]["config"]):
        raise ValueError("Runs must use matching checkpoint revision and preprocessing config.")
    # Include Python imports and loading both models; keep separate from warmed inference.
    started = time.perf_counter()
    predictor = PhoBERTCPU(run_dirs, runs, threads)
    load_seconds = time.perf_counter() - started
    import psutil
    memory = psutil.Process().memory_info()
    report = {
        "model": "phobert", "mode": "benchmark" if benchmark else "reload-verification",
        "environment": environment(),
        "hardware": {"processor": platform.processor(), "logical_cpus": os.cpu_count(),
                     "total_ram_bytes": psutil.virtual_memory().total},
        "cpu_threads": threads, "interop_threads": 1, "batch_size": 1,
        "dataset_revision": manifest["revision"], "dataset_sha256": manifest["sha256"],
        "model_revision": runs["sentiment"]["model_revision"],
        "run_directories": {task: path.name for task, path in run_dirs.items()},
        "files_sha256": hashes, "load_seconds_including_imports": round(load_seconds, 3),
        "rss_after_load_bytes": memory.rss,
        "weights_size_bytes": sum((p / "best_model/model.safetensors").stat().st_size
                                  for p in run_dirs.values()),
    }
    if benchmark:
        texts = [row["sentence"] for row in data["test"][:samples]]
        print(f"Benchmark: {len(texts)} test texts; joint CPU inference; threads={threads}", flush=True)
        report.update(
            scope="normalize + PyVi + tokenization + joint softmax; CPU; batch=1; excludes DB/HTTP/load",
            split="test", sample_selection="first N in verified snapshot order", warmup_runs=5,
            benchmarks=benchmark_cpu_latency(predictor.predict, texts),
        )
    else:
        rows = data["validation"][:samples]
        exported = {task: json.loads((path / "predictions.json").read_text())["validation"]
                    for task, path in run_dirs.items()}
        mismatches = {task: [] for task in run_dirs}
        for index, row in enumerate(rows):
            predicted = predictor.predict(row["sentence"])
            for task in run_dirs:
                if predicted[task]["label_id"] != exported[task][index]:
                    mismatches[task].append(index)
            if (index + 1) % 32 == 0:
                print(f"Reload check: {index + 1}/{len(rows)} validation texts", flush=True)
        report.update(
            split="validation", checked_samples=len(rows),
            sample_selection="first N in verified snapshot order; not full evaluation unless N=1583",
            mismatched_indices=mismatches, labels_match_export=not any(mismatches.values()),
            status="passed" if not any(mismatches.values()) else "failed",
        )
    memory = psutil.Process().memory_info()
    report["rss_after_inference_bytes"] = memory.rss
    report["peak_rss_bytes"] = getattr(memory, "peak_wset", None)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)
    print(f"Saved CPU evidence: {output}", flush=True)
    if not benchmark and report["status"] != "passed":
        raise ValueError("Reloaded predictions differ from GPU export; inspect mismatch indices.")
