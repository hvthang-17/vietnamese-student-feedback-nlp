"""Import trusted Colab results without loading pickle or replacing production."""
import hashlib
import json
import re
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

from backend.app.labels import SENTIMENT_LABELS, TOPIC_LABELS
from ml.core.runs import write_json
from ml.data.dataset import load_prepared
from ml.evaluation.metrics import build_task_metrics


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_run(read_json, manifest: dict, data: dict) -> dict:
    run = read_json("run.json")
    task = run.get("task")
    if run.get("model") != "phobert" or run.get("status") != "complete":
        raise ValueError("A completed PhoBERT run is required.")
    if task not in ("sentiment", "topic") or run.get("dataset") != manifest:
        raise ValueError("Task or dataset manifest mismatch.")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", str(run.get("model_revision", ""))):
        raise ValueError("A pinned model revision is required.")
    labels = SENTIMENT_LABELS if task == "sentiment" else TOPIC_LABELS
    config = read_json("best_model/config.json")
    if (config.get("model_type") != "roberta"
            or config.get("id2label") != {str(k): v for k, v in labels.items()}
            or config.get("label2id") != {v: k for k, v in labels.items()}):
        raise ValueError("Model architecture or label mapping mismatch.")
    if run["config"]["phobert"]["max_length"] != 128:
        raise ValueError("Unsupported truncation length; review preprocessing first.")
    predictions = read_json("predictions.json")
    metrics = read_json("metrics.json")
    if (metrics.get("dataset") != manifest or metrics.get("task") != task
            or metrics.get("model_revision") != run["model_revision"]
            or metrics.get("config") != run["config"]):
        raise ValueError("Metrics provenance mismatch.")
    for split in ("validation", "test"):
        predicted = predictions[split]
        if (len(predicted) != len(data[split])
                or any(type(x) is not int or x not in labels for x in predicted)):
            raise ValueError("Invalid prediction count or labels.")
        actual = build_task_metrics([row[task] for row in data[split]], predicted, task)
        if actual != metrics[split][task]:
            raise ValueError("Exported metrics do not match snapshot labels and predictions.")
    return run


def import_run(archive: Path, data_dir: Path, runs_root: Path) -> Path:
    data, manifest = load_prepared(data_dir)
    with zipfile.ZipFile(archive) as source:
        members = source.infolist()
        if len(members) > 100 or sum(m.file_size for m in members) > 2_000_000_000:
            raise ValueError("Archive exceeds result size limits.")
        names = set()
        roots = set()
        for member in members:
            name = member.filename
            parts = PurePosixPath(name).parts
            if (not parts or name.startswith("/") or "\\" in name or ":" in name
                    or any(p in (".", "..") for p in parts) or name in names
                    or stat.S_ISLNK(member.external_attr >> 16)
                    or member.file_size > 600_000_000):
                raise ValueError("Unsafe, duplicated or oversized archive member.")
            names.add(name)
            roots.add(parts[0])
        if len(roots) != 1:
            raise ValueError("Expected one run directory in the archive.")
        root = roots.pop()
        if not re.fullmatch(r"phobert-(sentiment|topic)-[A-Za-z0-9-]+", root):
            raise ValueError("Unsupported run directory name.")
        target = runs_root / root
        if target.exists():
            raise FileExistsError(target)
        run = validate_run(lambda rel: json.loads(source.read(f"{root}/{rel}")), manifest, data)
        if not root.startswith(f"phobert-{run['task']}-"):
            raise ValueError("Archive name and task disagree.")
        required = {"model.safetensors", "config.json", "vocab.txt", "bpe.codes",
                    "tokenizer_config.json", "special_tokens_map.json"}
        if any(f"{root}/best_model/{name}" not in names for name in required):
            raise ValueError("Missing model or tokenizer files.")
        if source.testzip() is not None:
            raise ValueError("ZIP CRC verification failed.")
        target.mkdir(parents=True, exist_ok=False)
        hashes = {}
        skipped = []
        # Deliberately exclude training_args.bin: inference never needs this pickle.
        for member in members:
            rel = PurePosixPath(member.filename).relative_to(root)
            if member.is_dir():
                continue
            allowed = (str(rel) in {"run.json", "metrics.json", "predictions.json"}
                       or (rel.parts[0] == "best_model" and rel.name in required | {"added_tokens.json"})
                       or (rel.parts[0] == "checkpoints" and rel.name == "trainer_state.json"))
            if not allowed:
                skipped.append(str(rel))
                continue
            destination = target.joinpath(*rel.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with source.open(member) as incoming, destination.open("xb") as outgoing:
                shutil.copyfileobj(incoming, outgoing)
            hashes[str(rel)] = sha256(destination)
        write_json(target / "import.json", {
            "schema_version": 1, "archive": archive.name, "archive_sha256": sha256(archive),
            "files_sha256": hashes, "skipped": skipped, "status": "complete",
            "metrics_recomputed_match": True, "inference_verified": False,
        })
    print(f"Imported {run['task']}: {target}; production unchanged.")
    return target


def check_import(run_dir: Path, manifest: dict, data: dict) -> tuple[dict, dict]:
    receipt = json.loads((run_dir / "import.json").read_text(encoding="utf-8"))
    if receipt.get("status") != "complete":
        raise ValueError("Incomplete import.")
    hashes = receipt["files_sha256"]
    required = {"run.json", "metrics.json", "predictions.json", "best_model/model.safetensors",
                "best_model/config.json", "best_model/tokenizer_config.json",
                "best_model/special_tokens_map.json", "best_model/vocab.txt", "best_model/bpe.codes"}
    if not required.issubset(hashes):
        raise ValueError("Import receipt is missing required hashes.")
    for rel, expected in hashes.items():
        path = PurePosixPath(rel)
        if path.is_absolute() or ".." in path.parts or "\\" in rel or ":" in rel:
            raise ValueError("Unsafe receipt path.")
        if sha256(run_dir.joinpath(*path.parts)) != expected:
            raise ValueError(f"Imported file checksum mismatch: {rel}")
    run = validate_run(lambda rel: json.loads((run_dir / rel).read_text(encoding="utf-8")), manifest, data)
    return run, hashes
