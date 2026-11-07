"""Bounded CSV validation followed by one atomic write of valid rows."""
import csv
import io
from pydantic import ValidationError

from ..domain.models import InputError, ResourceLimitError, Source
from ..schemas import PredictionRequest
from ..settings import Settings
from .feedback import FeedbackService


class ImportService:
    def __init__(self, feedback: FeedbackService, settings: Settings):
        self.feedback = feedback
        self.settings = settings

    def import_csv(self, content: bytes) -> dict:
        if len(content) > self.settings.max_csv_bytes:
            raise ResourceLimitError("CSV vượt giới hạn dung lượng cho phép.")
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise InputError("CSV phải dùng mã hóa UTF-8.") from exc
        reader = csv.DictReader(io.StringIO(decoded, newline=""), strict=True)
        try:
            headers = reader.fieldnames
        except csv.Error as exc:
            raise InputError("CSV header không đúng cấu trúc.") from exc
        if not headers or "text" not in headers:
            raise InputError("CSV phải có cột text.")
        if len(set(headers)) != len(headers):
            raise InputError("CSV không được có tên cột trùng nhau.")
        items, errors, count = [], [], 0
        try:
            for number, row in enumerate(reader, start=2):
                count += 1
                if count > self.settings.max_csv_rows:
                    raise ResourceLimitError("CSV vượt giới hạn số dòng cho phép.")
                if None in row:
                    errors.append({"row": number, "message": "Số cột không khớp header."})
                    continue
                try:
                    payload = PredictionRequest(text=row.get("text"), created_at=row.get("created_at") or None)
                except ValidationError as exc:
                    errors.append({"row": number, "message": exc.errors(include_input=False)[0]["msg"]})
                    continue
                items.append((payload.text, payload.created_at))
        except csv.Error as exc:
            raise InputError("CSV không đúng cấu trúc hoặc có ô quá dài.") from exc
        if not count:
            raise InputError("CSV cần ít nhất một dòng dữ liệu.")
        results = self.feedback.predict_many(items, Source.CSV) if items else []
        return {"imported": len(results), "errors": errors}
