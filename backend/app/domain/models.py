"""Domain values shared by application services and adapters."""
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum

from ..labels import SENTIMENT_LABELS, TOPIC_LABELS


class Sentiment(StrEnum):
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"


class Topic(StrEnum):
    LECTURER = "lecturer"
    TRAINING_PROGRAM = "training_program"
    FACILITY = "facility"
    OTHERS = "others"


class Source(StrEnum):
    MANUAL = "manual"
    BATCH = "batch"
    CSV = "csv"


def utc_timestamp(value: datetime | None = None) -> str:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


class ModelContractError(RuntimeError):
    """An adapter returned a value outside the supported prediction contract."""


class ResourceLimitError(ValueError):
    pass


class InputError(ValueError):
    """A safe, user-facing input message, without raw feedback values."""


class ReportUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class Prediction:
    text: str
    sentiment_label: str
    sentiment_confidence: float
    topic_label: str
    topic_confidence: float
    model_version: str

    def __post_init__(self):
        if (self.sentiment_label not in SENTIMENT_LABELS.values()
                or self.topic_label not in TOPIC_LABELS.values()):
            raise ModelContractError("Invalid prediction label")
        for value in (self.sentiment_confidence, self.topic_confidence):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ModelContractError("Invalid prediction confidence")
        if not isinstance(self.model_version, str) or not self.model_version.strip():
            raise ModelContractError("Missing model version")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class FeedbackWrite:
    raw_text: str
    prediction: Prediction
    source: Source
    created_at: str | None
    received_at: str
    predicted_at: str


@dataclass(frozen=True)
class FeedbackFilter:
    sentiment: Sentiment | None = None
    topic: Topic | None = None
    predicted_from: datetime | None = None
    predicted_to: datetime | None = None

    def __post_init__(self):
        for value in (self.predicted_from, self.predicted_to):
            if value is not None:
                utc_timestamp(value)
        if (self.predicted_from and self.predicted_to
                and self.predicted_from >= self.predicted_to):
            raise ValueError("predicted_from must be earlier than predicted_to")
