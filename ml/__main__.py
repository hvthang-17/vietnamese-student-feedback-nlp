"""Single stage-oriented command line; heavy ML imports are lazy."""
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="UIT-VSFC: prepare -> eda -> train -> benchmark -> promote")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Download official Parquet and save a checked snapshot")
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--revision", default="refs/convert/parquet", help="Parquet branch or commit; resolved to a commit")
    eda = commands.add_parser("eda", help="Describe a prepared snapshot")
    eda.add_argument("--data-dir", type=Path, required=True)
    eda.add_argument("--output", type=Path, required=True)
    for name in ("train-baseline", "train-phobert"):
        train = commands.add_parser(name, help="Train into a NEW experiment directory")
        train.add_argument("--data-dir", type=Path, required=True)
        train.add_argument("--run-dir", type=Path, required=True)
        if name == "train-phobert":
            train.add_argument("--task", choices=["sentiment", "topic"], required=True)
            train.add_argument("--model-revision", required=True, help="Pinned checkpoint commit")
    benchmark = commands.add_parser("benchmark", help="Measure a completed baseline run on CPU")
    benchmark.add_argument("--data-dir", type=Path, required=True)
    benchmark.add_argument("--run-dir", type=Path, required=True)
    benchmark.add_argument("--output", type=Path, required=True)
    importer = commands.add_parser("import-phobert", help="Import a trusted result ZIP without overwriting runs")
    importer.add_argument("--archive", type=Path, required=True)
    importer.add_argument("--data-dir", type=Path, required=True)
    importer.add_argument("--runs-root", type=Path, default=Path("artifacts/runs"))
    for name in ("verify-phobert", "benchmark-phobert"):
        cpu = commands.add_parser(name, help="Reload local safetensors and verify or benchmark on CPU")
        cpu.add_argument("--data-dir", type=Path, required=True)
        cpu.add_argument("--sentiment-run", type=Path, required=True)
        cpu.add_argument("--topic-run", type=Path, required=True)
        cpu.add_argument("--output", type=Path, required=True)
        cpu.add_argument("--samples", type=int, default=64 if name == "verify-phobert" else 300)
        cpu.add_argument("--threads", type=int, default=1)
    promote = commands.add_parser("promote", help="Explicitly copy an eligible baseline artifact to the API")
    promote.add_argument("--run-dir", type=Path, required=True)
    promote.add_argument("--benchmark", type=Path, required=True)
    promote.add_argument("--replace", action="store_true", help="Allow replacement of existing production.joblib")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            from ml.data.dataset import prepare
            prepare(args.output, args.revision)
        elif args.command == "eda":
            from ml.data.eda import describe
            describe(args.data_dir, args.output)
        elif args.command == "train-baseline":
            from ml.training.baseline import train
            train(args.data_dir, args.run_dir)
        elif args.command == "train-phobert":
            from ml.training.phobert import train
            train(args.data_dir, args.run_dir, args.task, args.model_revision)
        elif args.command == "benchmark":
            from ml.evaluation.benchmark import benchmark
            benchmark(args.data_dir, args.run_dir, args.output)
        elif args.command == "import-phobert":
            from ml.deployment.import_phobert import import_run
            import_run(args.archive, args.data_dir, args.runs_root)
        elif args.command in ("verify-phobert", "benchmark-phobert"):
            from ml.evaluation.phobert import evaluate_cpu
            evaluate_cpu(args.data_dir, args.sentiment_run, args.topic_run, args.output,
                         args.samples, args.threads, args.command == "benchmark-phobert")
        else:
            from ml.deployment.promote import promote
            promote(args.run_dir, args.benchmark, args.replace)
    except (OSError, ValueError, ImportError, RuntimeError) as exc:
        parser.exit(1, f"{args.command} failed: {exc}\n")


if __name__ == "__main__":
    main()
