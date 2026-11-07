"""Download a pinned official dataset once; verify local snapshots before reuse."""
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from backend.app.preprocessing import normalize_text
from ml.core.config import get_config
from ml.core.runs import write_json

SPLITS = ("train", "validation", "test")


def validate_splits(data: dict, expected_counts: dict | None = None) -> dict:
    """Reject bad schemas/labels; report duplicates without altering canonical splits."""
    sets, report = {}, {}
    for split in SPLITS:
        rows = data[split]
        if not rows:
            raise ValueError(f"Empty split: {split}")
        if expected_counts and len(rows) != expected_counts[split]:
            raise ValueError(f"Unexpected {split} count: {len(rows)}")
        for row in rows:
            if not isinstance(row.get("sentence"), str):
                raise ValueError(f"Invalid sentence in {split}")
            if normalize_text(row["sentence"]) != row["sentence"]:
                raise ValueError(f"Unnormalized sentence in {split}")
            for key, allowed in (("sentiment", range(3)), ("topic", range(4))):
                if type(row.get(key)) is not int or row[key] not in allowed:
                    raise ValueError(f"Invalid {key} label in {split}")
        texts = [row["sentence"] for row in rows]
        sets[split] = set(texts)
        report[split] = {
            "count": len(rows),
            "duplicate_rows": len(rows) - len(sets[split]),
            "sentiment": dict(Counter(row["sentiment"] for row in rows)),
            "topic": dict(Counter(row["topic"] for row in rows)),
        }
    report["overlap_unique_texts"] = {
        f"{a}:{b}": len(sets[a] & sets[b]) for a, b in combinations(SPLITS, 2)
    }
    return report


def prepare(output: Path, revision: str) -> None:
    if output.exists():
        raise FileExistsError(f"Choose a new snapshot directory: {output}")
    from datasets import load_dataset
    from huggingface_hub import HfApi

    cfg = get_config()
    # Resolve even branch references to an immutable dataset commit before downloading.
    commit = HfApi().dataset_info(cfg.dataset_name, revision=revision).sha
    urls = {
        split: f"https://huggingface.co/datasets/{cfg.dataset_name}/resolve/{commit}/default/{split}/0000.parquet"
        for split in SPLITS
    }
    dataset = load_dataset("parquet", data_files=urls)
    data = {
        split: [
            {"sentence": normalize_text(row["sentence"]),
             "sentiment": row["sentiment"], "topic": row["topic"]}
            for row in dataset[split]
        ] for split in SPLITS
    }
    validation = validate_splits(data, cfg.split_counts)
    output.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for split, rows in data.items():
        path = output / f"{split}.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        hashes[split] = hashlib.sha256(path.read_bytes()).hexdigest()
    write_json(output / "manifest.json", {
        "schema_version": 1, "source": "huggingface", "dataset_name": cfg.dataset_name,
        "revision": commit, "requested_revision": revision,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "preprocessing": cfg.to_dict()["preprocessing"],
        "sha256": hashes, "validation": validation,
    })
    print(f"Prepared snapshot: {output}; revision={commit}")
    print(f"Exact normalized-text overlap: {validation['overlap_unique_texts']}")


def load_prepared(directory: Path) -> tuple[dict, dict]:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    cfg = get_config()
    if (manifest.get("schema_version") != 1 or manifest.get("source") != "huggingface"
            or manifest.get("dataset_name") != cfg.dataset_name
            or not re.fullmatch(r"[0-9a-fA-F]{40}", str(manifest.get("revision", "")))
            or manifest.get("preprocessing") != cfg.to_dict()["preprocessing"]):
        raise ValueError("Not a supported official dataset snapshot. Run prepare first.")
    data = {}
    for split in SPLITS:
        raw = (directory / f"{split}.jsonl").read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["sha256"][split]:
            raise ValueError(f"Snapshot checksum mismatch: {split}")
        data[split] = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    current = validate_splits(data, cfg.split_counts)
    # JSON serializes integer histogram keys as strings.
    if json.loads(json.dumps(current)) != manifest["validation"]:
        raise ValueError("Snapshot validation report does not match its data.")
    return data, manifest
