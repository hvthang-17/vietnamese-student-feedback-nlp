"""Validation tuning and calibrated baseline training; no production writes."""
import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC
from typing import Any, Dict
from backend.app.labels import SENTIMENT_LABELS, TOPIC_LABELS
from ml.core.config import get_config
from ml.core.runs import create_run, write_json
from ml.data.dataset import load_prepared
from ml.evaluation.metrics import create_standard_metrics_report

def build_vectorizer(use_char_ngram: bool = False):
    """Build word vectorizer or composite word+char feature union."""
    cfg = get_config().baseline
    word_vec = TfidfVectorizer(
        analyzer="word",
        ngram_range=cfg.ngram_range,
        min_df=cfg.min_df,
        max_df=cfg.max_df,
        sublinear_tf=cfg.sublinear_tf,
    )
    if not use_char_ngram:
        return word_vec

    char_vec = TfidfVectorizer(
        analyzer="char",
        ngram_range=(3, 5),
        min_df=5,
        max_df=cfg.max_df,
        sublinear_tf=cfg.sublinear_tf,
    )
    return FeatureUnion([("word", word_vec), ("char", char_vec)])


def evaluate_candidate(
    train_texts, train_labels, val_texts, val_labels, use_char_ngram: bool, c_val: float, class_weight: str | None
) -> float:
    """Train uncalibrated SVM candidate on Train set and evaluate Macro F1 on Validation set."""
    vec = build_vectorizer(use_char_ngram)
    svc = LinearSVC(C=c_val, class_weight=class_weight, random_state=get_config().random_seed, dual="auto")
    pipe = Pipeline([("vectorizer", vec), ("classifier", svc)])
    pipe.fit(train_texts, train_labels)
    preds = pipe.predict(val_texts)
    return float(f1_score(val_labels, preds, average="macro"))


def run_ngram_ablation_and_tuning(train_texts, train_labels, val_texts, val_labels, task_name: str) -> Dict[str, Any]:
    """Perform n-gram ablation study and grid search strictly on Validation set."""
    print(f"\n[TUNING] Bắt đầu tinh chỉnh siêu tham số và khảo sát n-gram cho tác vụ: {task_name.upper()}")

    # 1. Ablation: Word n-gram (1,2) vs Word + Char n-gram (3,5)
    f1_word = evaluate_candidate(train_texts, train_labels, val_texts, val_labels, use_char_ngram=False, c_val=1.0, class_weight="balanced")
    f1_char = evaluate_candidate(train_texts, train_labels, val_texts, val_labels, use_char_ngram=True, c_val=1.0, class_weight="balanced")

    print(f"  - Word n-gram (1, 2) Val Macro F1: {f1_word:.4f}")
    print(f"  - Word + Char n-gram (3, 5) Val Macro F1: {f1_char:.4f}")

    # Requirement: "bổ sung character n-gram 3–5 chỉ khi validation cải thiện"
    use_char = bool(f1_char > f1_word + 0.002)
    print(f"  --> Quyết định n-gram: {'Bổ sung Char n-gram (3, 5)' if use_char else 'Chỉ dùng Word n-gram (1, 2)'}")

    # 2. Hyperparameter Grid Search on Validation set
    c_candidates = get_config().baseline.c_candidates
    weight_candidates = get_config().baseline.weight_candidates

    best_score = -1.0
    best_params = {}
    tuning_log = []

    for c in c_candidates:
        for cw in weight_candidates:
            score = evaluate_candidate(train_texts, train_labels, val_texts, val_labels, use_char_ngram=use_char, c_val=c, class_weight=cw)
            tuning_log.append({"c": c, "class_weight": cw, "val_macro_f1": round(score, 4)})
            if score > best_score:
                best_score = score
                best_params = {"c": c, "class_weight": cw, "use_char_ngram": use_char}

    print(f"  --> Cấu hình tốt nhất: C={best_params['c']}, class_weight={best_params['class_weight']} (Val Macro F1 = {best_score:.4f})")

    return {
        "best_params": best_params,
        "best_val_macro_f1": round(best_score, 4),
        "ablation": {
            "word_ngram_macro_f1": round(f1_word, 4),
            "word_char_ngram_macro_f1": round(f1_char, 4),
            "char_ngram_selected": use_char,
        },
        "grid_search_log": tuning_log,
    }


def train_and_calibrate_pipeline(train_texts, train_labels, best_params: Dict[str, Any]):
    """Fit final model on train set with probability calibration (CalibratedClassifierCV)."""
    vec = build_vectorizer(use_char_ngram=best_params["use_char_ngram"])
    svc = LinearSVC(
        C=best_params["c"],
        class_weight=best_params["class_weight"],
        random_state=get_config().random_seed,
        dual="auto",
    )
    pipeline = CalibratedClassifierCV(
        estimator=Pipeline([("vectorizer", vec), ("classifier", svc)]),
        cv=get_config().baseline.calibration_cv,
        method=get_config().baseline.calibration_method,
    )
    pipeline.fit(train_texts, train_labels)
    return pipeline



def train(data_dir, run_dir):
    """Tune on validation, evaluate the final calibrated models once on test."""
    import hashlib
    data, manifest = load_prepared(data_dir)
    cfg = get_config()
    metadata = create_run(run_dir, "baseline", manifest, cfg.to_dict())
    models, tuning = {}, {}
    for task in ("sentiment", "topic"):
        train_rows, val_rows = data["train"], data["validation"]
        tuning[task] = run_ngram_ablation_and_tuning(
            [r["sentence"] for r in train_rows], [r[task] for r in train_rows],
            [r["sentence"] for r in val_rows], [r[task] for r in val_rows], task,
        )
        models[task] = train_and_calibrate_pipeline(
            [r["sentence"] for r in train_rows], [r[task] for r in train_rows],
            tuning[task]["best_params"],
        )
    predictions = {
        split: {task: models[task].predict([r["sentence"] for r in data[split]]).tolist()
                for task in models} for split in ("validation", "test")
    }
    version = "baseline-" + run_dir.name
    artifact = run_dir / "model.joblib"
    joblib.dump({
        "model_version": version, "model_type": "sklearn_calibrated_pipeline",
        "sentiment_model": models["sentiment"], "topic_model": models["topic"],
        "label_mappings": {"sentiment": SENTIMENT_LABELS, "topic": TOPIC_LABELS},
        "dataset": manifest, "config": cfg.to_dict(), "tuning_metadata": tuning,
    }, artifact, compress=3)
    report = create_standard_metrics_report(
        model_name="tfidf-linear-svm", model_version=version,
        val_sentiment_true=[r["sentiment"] for r in data["validation"]],
        val_sentiment_pred=predictions["validation"]["sentiment"],
        val_topic_true=[r["topic"] for r in data["validation"]],
        val_topic_pred=predictions["validation"]["topic"],
        test_sentiment_true=[r["sentiment"] for r in data["test"]],
        test_sentiment_pred=predictions["test"]["sentiment"],
        test_topic_true=[r["topic"] for r in data["test"]],
        test_topic_pred=predictions["test"]["topic"], benchmarks={},
        artifact_size_bytes=artifact.stat().st_size,
        extra_metadata={"data_source": manifest["source"], "dataset": manifest, "tuning": tuning},
    )
    write_json(run_dir / "metrics.json", report)
    write_json(run_dir / "predictions.json", predictions)
    metadata.update(status="complete", model_version=version,
                    artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    metrics_sha256=hashlib.sha256((run_dir / "metrics.json").read_bytes()).hexdigest())
    write_json(run_dir / "run.json", metadata)
    print(f"Baseline completed: {run_dir}. Benchmark and promote are separate steps.")
