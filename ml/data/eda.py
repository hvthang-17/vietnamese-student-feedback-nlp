"""Measured statistics from a verified snapshot; no estimated fallback values."""
import statistics
from pathlib import Path
from ml.core.runs import write_json
from ml.data.dataset import load_prepared, SPLITS


def describe(directory: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    data, manifest = load_prepared(directory)
    report = {"dataset": manifest, "splits": {}}
    for split in SPLITS:
        rows = data[split]
        matrix = [[0] * 3 for _ in range(4)]
        for row in rows:
            matrix[row["topic"]][row["sentiment"]] += 1
        lengths = {}
        for name, values in (
            ("characters", [len(row["sentence"]) for row in rows]),
            ("whitespace_units", [len(row["sentence"].split()) for row in rows]),
        ):
            lengths[name] = {"min": min(values), "max": max(values),
                             "mean": statistics.mean(values), "median": statistics.median(values)}
        report["splits"][split] = {"lengths": lengths, "topic_sentiment_matrix": matrix}
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)
    print(f"Measured EDA report: {output}")
