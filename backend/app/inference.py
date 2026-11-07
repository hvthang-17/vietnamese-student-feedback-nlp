from pathlib import Path
from typing import Any

from .labels import SENTIMENT_LABELS, TOPIC_LABELS
from .preprocessing import normalize_text

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts"


def load_predictor(settings):
    if settings.model_backend == "phobert":
        from .phobert import PhoBERTService
        return PhoBERTService(settings.phobert_sentiment_run, settings.phobert_topic_run,
                              settings.phobert_cpu_threads)
    return InferenceService(settings.model_path, allow_demo=settings.allow_demo_model,
                            require_official=settings.environment == "production")


class InferenceService:
    """Uses calibrated sklearn artifacts when present; otherwise a deterministic demo fallback."""
    def __init__(self, artifact_path: Path | None = None, allow_demo: bool = True,
                 require_official: bool = False) -> None:
        self.model_version = "demo-keyword-v1"
        self.sentiment_model: Any = None
        self.topic_model: Any = None
        manifest = artifact_path if artifact_path is not None else ARTIFACTS / "production.joblib"
        if manifest.exists():
            import joblib
            bundle = joblib.load(manifest)
            if require_official and bundle.get("dataset", {}).get("source") != "huggingface":
                raise ValueError("Production requires official-dataset provenance; legacy artifacts are not eligible")
            self.sentiment_model = bundle["sentiment_model"]
            self.topic_model = bundle["topic_model"]
            self.model_version = bundle.get("model_version", "sklearn-production")
            for model in (self.sentiment_model, self.topic_model):
                if not callable(getattr(model, "predict_proba", None)) or not hasattr(model, "classes_"):
                    raise ValueError("Unsupported model artifact interface")
        elif not allow_demo:
            raise FileNotFoundError("Model artifact is required when demo mode is disabled")

    @property
    def is_fallback(self) -> bool:
        return self.sentiment_model is None

    def predict(self, text: str) -> dict[str, Any]:
        text = normalize_text(text)
        if not self.is_fallback:
            sentiment_probs = self.sentiment_model.predict_proba([text])[0]
            topic_probs = self.topic_model.predict_proba([text])[0]
            sentiment_id = int(self.sentiment_model.classes_[sentiment_probs.argmax()])
            topic_id = int(self.topic_model.classes_[topic_probs.argmax()])
            return {
                "text": text, "sentiment_label": SENTIMENT_LABELS[sentiment_id],
                "sentiment_confidence": float(sentiment_probs.max()), "topic_label": TOPIC_LABELS[topic_id],
                "topic_confidence": float(topic_probs.max()), "model_version": self.model_version,
            }
        lower = text.lower()
        negative = ("không", "tệ", "kém", "chán", "quá ít", "khó", "trễ", "thiếu")
        positive = ("tốt", "hay", "nhiệt tình", "tận tâm", "hài lòng", "dễ hiểu", "đầy đủ")
        if any(word in lower for word in negative):
            sentiment, sc = "negative", 0.65
        elif any(word in lower for word in positive):
            sentiment, sc = "positive", 0.70
        else:
            sentiment, sc = "neutral", 0.55
        if any(word in lower for word in ("wifi", "phòng", "máy", "thiết bị", "cơ sở vật chất")):
            topic = "facility"
        elif any(word in lower for word in ("thầy", "cô", "giảng viên", "giáo viên")):
            topic = "lecturer"
        elif any(word in lower for word in ("môn", "bài tập", "slide", "giáo trình", "chương trình", "lớp")):
            topic = "training_program"
        else:
            topic = "others"
        return {"text": text, "sentiment_label": sentiment, "sentiment_confidence": sc,
                "topic_label": topic, "topic_confidence": 0.60, "model_version": self.model_version}
