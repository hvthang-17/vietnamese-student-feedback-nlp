"""Application use cases depend on ports, not global model/database instances."""
from datetime import datetime
from ..domain.models import FeedbackFilter, FeedbackWrite, InputError, ModelContractError, Prediction, Source, utc_timestamp
from ..domain.ports import FeedbackStore, Predictor
from ..preprocessing import normalize_text


class FeedbackService:
    def __init__(self, repository: FeedbackStore, predictor: Predictor):
        self.repository = repository
        self.predictor = predictor

    def predict_many(self, items: list[tuple[str, datetime | None]], source: Source) -> list[dict]:
        records = []
        for raw_text, created_at in items:
            received_at = utc_timestamp()
            if not isinstance(raw_text, str) or not 1 <= len(raw_text) <= 5000:
                raise InputError("Phản hồi phải có từ 1 đến 5000 ký tự.")
            try:
                normalized = normalize_text(raw_text)
            except ValueError as exc:
                raise InputError("Nội dung phản hồi không được để trống.") from exc
            if len(normalized) > 5000:
                raise InputError("Nội dung sau chuẩn hóa vượt quá 5000 ký tự.")
            output = self.predictor.predict(normalized)
            try:
                prediction = Prediction(**output)
            except (TypeError, ValueError) as exc:
                raise ModelContractError("Predictor returned an unsupported result") from exc
            if prediction.text != normalized:
                raise ModelContractError("Predictor must preserve normalized input")
            records.append(FeedbackWrite(raw_text, prediction, source,
                                         utc_timestamp(created_at) if created_at else None,
                                         received_at, utc_timestamp()))
        # Inference finishes before acquiring the database writer lock.
        return self.repository.save_many(records)

    def predict(self, text: str, created_at: datetime | None = None) -> dict:
        return self.predict_many([(text, created_at)], Source.MANUAL)[0]

    def feedback(self, filters: FeedbackFilter, page: int, page_size: int) -> dict:
        return self.repository.list_page(filters, page, page_size)

    def get(self, feedback_id: int) -> dict | None:
        return self.repository.get(feedback_id)

    def summary(self, filters: FeedbackFilter) -> dict:
        return self.repository.summary(filters)
