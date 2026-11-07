"""HTTP contracts; domain and repository layers do not depend on Pydantic."""
from datetime import datetime
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator
from .domain.models import Sentiment, Source, Topic


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=5000)
    created_at: AwareDatetime | None = None

    @field_validator("text")
    @classmethod
    def valid_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Nội dung phản hồi không được để trống.")
        if "\x00" in value:
            raise ValueError("Phản hồi không được chứa ký tự NUL.")
        return value


class BatchPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[PredictionRequest] = Field(min_length=1, max_length=100)


class PredictionResponse(BaseModel):
    feedback_id: int
    raw_text: str
    text: str
    sentiment_label: Sentiment
    sentiment_confidence: float = Field(ge=0, le=1)
    topic_label: Topic
    topic_confidence: float = Field(ge=0, le=1)
    model_version: str
    predicted_at: datetime


class FeedbackRecord(BaseModel):
    id: int
    raw_text: str
    text: str
    source: Source
    created_at: str | None
    received_at: datetime
    sentiment_label: Sentiment
    sentiment_confidence: float = Field(ge=0, le=1)
    topic_label: Topic
    topic_confidence: float = Field(ge=0, le=1)
    model_version: str
    predicted_at: datetime


class FeedbackPage(BaseModel):
    items: list[FeedbackRecord]
    total: int
    page: int
    page_size: int


class DashboardSummary(BaseModel):
    total: int
    sentiment: dict[str, int]
    topic: dict[str, int]
    matrix: dict[str, dict[str, int]]
    has_timestamps: bool


class ImportErrorRow(BaseModel):
    row: int
    message: str


class ImportResult(BaseModel):
    imported: int
    errors: list[ImportErrorRow]


class HealthResponse(BaseModel):
    status: str
    model_version: str
    fallback_model: bool


class ErrorResponse(BaseModel):
    detail: str
