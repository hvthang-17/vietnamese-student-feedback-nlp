"""Settings actually consumed by the experiment stages."""
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PreprocessingConfig:
    unicode_form: str = "NFC"
    collapse_whitespace: bool = True
    preserve_casing: bool = True
    strip_margins: bool = True


@dataclass(frozen=True)
class BaselineConfig:
    ngram_range: tuple[int, int] = (1, 2)
    min_df: int = 2
    max_df: float = 0.95
    sublinear_tf: bool = True
    calibration_cv: int = 3
    calibration_method: str = "sigmoid"
    c_candidates: tuple[float, ...] = (0.5, 1.0, 2.0)
    weight_candidates: tuple = ("balanced", None)


@dataclass(frozen=True)
class PhoBERTConfig:
    pretrained_model_name: str = "vinai/phobert-base"
    max_length: int = 128
    batch_size: int = 8
    eval_batch_size: int = 16
    learning_rate: float = 2e-5
    num_train_epochs: int = 5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    metric_for_best_model: str = "macro_f1"
    early_stopping_patience: int = 2


@dataclass(frozen=True)
class ExperimentConfig:
    random_seed: int = 42
    dataset_name: str = "uitnlp/vietnamese_students_feedback"
    split_counts: dict[str, int] = field(default_factory=lambda: {
        "train": 11426, "validation": 1583, "test": 3166, "total": 16175,
    })
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    baseline: BaselineConfig = field(default_factory=BaselineConfig)
    phobert: PhoBERTConfig = field(default_factory=PhoBERTConfig)
    target_macro_f1_sentiment: float = 0.80
    target_macro_f1_topic: float = 0.75
    max_p95_cpu_latency_ms: float = 2000.0

    def to_dict(self) -> dict:
        return asdict(self)


GLOBAL_CONFIG = ExperimentConfig()


def get_config() -> ExperimentConfig:
    return GLOBAL_CONFIG
