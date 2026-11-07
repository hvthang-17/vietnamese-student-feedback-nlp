"""Explicit, non-overwriting experiment directories and JSON output."""
import json
import platform
from importlib.metadata import PackageNotFoundError, version
from datetime import datetime, timezone
from pathlib import Path


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def environment() -> dict:
    packages = {}
    for name in ("numpy", "scikit-learn", "joblib", "datasets", "huggingface-hub",
                 "torch", "transformers", "pyvi", "accelerate"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            pass
    return {"python": platform.python_version(), "platform": platform.platform(),
            "processor": platform.processor(), "packages": packages}


def create_run(path: Path, model: str, dataset_manifest: dict, config: dict) -> dict:
    path.mkdir(parents=True, exist_ok=False)
    metadata = {
        "model": model,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset_manifest,
        "config": config,
        "environment": environment(),
        "status": "running",
    }
    write_json(path / "run.json", metadata)
    return metadata
