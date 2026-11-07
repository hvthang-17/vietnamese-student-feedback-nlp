"""Comprehensive tests for data pipeline reproducibility, label mapping, text normalization, and split integrity."""

import unicodedata
import pytest

from backend.app.labels import SENTIMENT_LABELS, TOPIC_LABELS, SENTIMENT_VI, TOPIC_VI
from backend.app.preprocessing import preprocess_text, normalize_text
from ml.core.config import get_config
from ml.evaluation.metrics import build_task_metrics, create_standard_metrics_report


# ============================================================================
# 1. Label Mapping Tests
# ============================================================================

def test_sentiment_label_mappings():
    """Verify sentiment label space has exactly 3 classes matching UIT-VSFC."""
    assert len(SENTIMENT_LABELS) == 3
    assert SENTIMENT_LABELS[0] == "negative"
    assert SENTIMENT_LABELS[1] == "neutral"
    assert SENTIMENT_LABELS[2] == "positive"
    assert set(SENTIMENT_LABELS.keys()) == {0, 1, 2}
    for label in SENTIMENT_LABELS.values():
        assert label in SENTIMENT_VI
        assert isinstance(SENTIMENT_VI[label], str) and len(SENTIMENT_VI[label]) > 0


def test_topic_label_mappings():
    """Verify topic label space has exactly 4 classes matching UIT-VSFC."""
    assert len(TOPIC_LABELS) == 4
    assert TOPIC_LABELS[0] == "lecturer"
    assert TOPIC_LABELS[1] == "training_program"
    assert TOPIC_LABELS[2] == "facility"
    assert TOPIC_LABELS[3] == "others"
    assert set(TOPIC_LABELS.keys()) == {0, 1, 2, 3}
    for label in TOPIC_LABELS.values():
        assert label in TOPIC_VI
        assert isinstance(TOPIC_VI[label], str) and len(TOPIC_VI[label]) > 0


# ============================================================================
# 2. Text Normalization and Preprocessing Pipeline Tests
# ============================================================================

def test_preprocess_text_retains_raw_and_normalized():
    """Verify that preprocess_text retains both unaltered raw_text and cleaned normalized_text."""
    raw = "   Thầy    giáo  dạy   rất  tâm   huyết,   slide bài   giảng hay!   \n"
    res = preprocess_text(raw)
    assert res["raw_text"] == raw
    assert res["normalized_text"] == "Thầy giáo dạy rất tâm huyết, slide bài giảng hay!"


def test_normalize_text_unicode_nfc():
    """Verify that decomposed NFD Vietnamese characters are converted to canonical NFC."""
    # 'e' + combining hook above (U+0309) = 'ẻ' in NFD
    nfd_text = "Th" + unicodedata.normalize("NFD", "ầ") + "y d" + unicodedata.normalize("NFD", "ạ") + "y hay"
    normalized = normalize_text(nfd_text)
    assert unicodedata.is_normalized("NFC", normalized)
    assert normalized == "Thầy dạy hay"


def test_normalize_text_preserves_vietnamese_characters():
    """Verify all Vietnamese specific vowels, tone marks and 'đ' are preserved."""
    sample = "Ăn quả nhớ kẻ trồng cây, đùm bọc yêu thương, cơ sở vật chất kỹ thuật"
    assert normalize_text(f"  {sample}  ") == sample


def test_preprocess_rejects_empty_and_invalid():
    """Verify edge cases: whitespace-only, newlines, empty, and non-strings."""
    with pytest.raises(ValueError, match="không được để trống"):
        preprocess_text("    ")
    with pytest.raises(ValueError, match="không được để trống"):
        preprocess_text("\n\t  \r")
    with pytest.raises(ValueError, match="Văn bản phải là chuỗi"):
        preprocess_text(None)
    with pytest.raises(ValueError, match="Văn bản phải là chuỗi"):
        preprocess_text(12345)


# ============================================================================
# 3. Split Integrity and Configuration Tests
# ============================================================================

def test_canonical_split_integrity():
    """Verify canonical sample counts and split proportions match UIT-VSFC specification."""
    cfg = get_config()
    counts = cfg.split_counts

    assert counts["train"] == 11426
    assert counts["validation"] == 1583
    assert counts["test"] == 3166
    assert counts["total"] == 16175
    assert counts["train"] + counts["validation"] + counts["test"] == counts["total"]

    # Verify split ratios
    train_ratio = counts["train"] / counts["total"]
    val_ratio = counts["validation"] / counts["total"]
    test_ratio = counts["test"] / counts["total"]

    assert 0.70 <= train_ratio <= 0.71
    assert 0.09 <= val_ratio <= 0.10
    assert 0.19 <= test_ratio <= 0.20


def test_experiment_config_reproducibility():
    """Verify that experiment configuration is frozen and reproducible with seed 42."""
    cfg = get_config()
    assert cfg.random_seed == 42
    assert cfg.dataset_name == "uitnlp/vietnamese_students_feedback"
    assert cfg.target_macro_f1_sentiment == 0.80
    assert cfg.target_macro_f1_topic == 0.75
    assert cfg.max_p95_cpu_latency_ms == 2000.0


# ============================================================================
# 4. Standard Metrics and Report Schema Tests
# ============================================================================

def test_standard_metrics_format():
    """Verify task metrics calculation produces complete schema (accuracy, macro_f1, per_class, confusion_matrix)."""
    y_true = [0, 1, 2, 0, 2, 1]
    y_pred = [0, 1, 2, 0, 1, 1]
    task_res = build_task_metrics(y_true, y_pred, "sentiment")

    assert "accuracy" in task_res
    assert "macro_f1" in task_res
    assert "weighted_f1" in task_res
    assert "per_class" in task_res
    assert "confusion_matrix" in task_res

    # Check all 3 sentiment classes exist in per_class
    assert set(task_res["per_class"].keys()) == {"negative", "neutral", "positive"}
    for c_name, c_metrics in task_res["per_class"].items():
        assert {"precision", "recall", "f1_score", "support"}.issubset(c_metrics.keys())

    # Check confusion matrix dimensions (3x3 for sentiment)
    assert len(task_res["confusion_matrix"]) == 3
    assert all(len(row) == 3 for row in task_res["confusion_matrix"])


def test_full_report_assembly_and_criteria():
    """Verify create_standard_metrics_report generates all required benchmark and acceptance fields."""
    report = create_standard_metrics_report(
        model_name="tfidf-linear-svm",
        model_version="tfidf-linear-svm-v1",
        val_sentiment_true=[0, 1, 2], val_sentiment_pred=[0, 1, 2],
        val_topic_true=[0, 1, 2, 3], val_topic_pred=[0, 1, 2, 3],
        test_sentiment_true=[0, 1, 2], test_sentiment_pred=[0, 1, 2],
        test_topic_true=[0, 1, 2, 3], test_topic_pred=[0, 1, 2, 3],
        benchmarks={"p95_cpu_latency_ms": 1.25, "mean_cpu_latency_ms": 1.10},
        artifact_size_bytes=1024 * 1024,
    )

    assert report["model_name"] == "tfidf-linear-svm"
    assert "environment" in report
    assert "validation" in report
    assert "test" in report
    assert "benchmarks" in report
    assert "acceptance_verification" in report
    assert report["acceptance_verification"]["sentiment_target_met"] is True
    assert report["acceptance_verification"]["topic_target_met"] is True
    assert report["acceptance_verification"]["latency_target_met"] is True
    assert report["acceptance_verification"]["all_criteria_met"] is True
