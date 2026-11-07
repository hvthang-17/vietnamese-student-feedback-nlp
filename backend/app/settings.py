"""Process-environment settings; importing this module has no runtime I/O."""
import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    if value.lower() not in {"true", "false", "1", "0"}:
        raise ValueError(f"{name} must be true/false or 1/0")
    return value.lower() in {"true", "1"}


@dataclass(frozen=True)
class Settings:
    database_path: Path = ROOT / "data/feedback.db"
    model_path: Path = ROOT / "artifacts/production.joblib"
    model_backend: str = "sklearn"
    phobert_sentiment_run: Path | None = None
    phobert_topic_run: Path | None = None
    phobert_cpu_threads: int = 1
    environment: str = "development"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    api_token: str | None = field(default=None, repr=False)
    allow_demo_model: bool = True
    auto_migrate: bool = True
    max_csv_bytes: int = 2 * 1024 * 1024
    max_csv_rows: int = 1000
    max_export_rows: int = 5000
    database_timeout: float = 5.0
    pdf_font_path: Path | None = None
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"

    def __post_init__(self):
        for name in ("database_path", "model_path", "pdf_font_path", "phobert_sentiment_run", "phobert_topic_run"):
            path = getattr(self, name)
            if path is not None:
                object.__setattr__(self, name, (ROOT / path).resolve())
        if self.model_backend not in {"sklearn", "phobert"}:
            raise ValueError("MODEL_BACKEND must be sklearn or phobert")
        if self.phobert_cpu_threads < 1 or self.phobert_cpu_threads > (os.cpu_count() or 1):
            raise ValueError("Invalid PHOBERT_CPU_THREADS")
        if self.model_backend == "phobert" and not (self.phobert_sentiment_run and self.phobert_topic_run):
            raise ValueError("PhoBERT requires both task run directories")
        if self.environment not in {"development", "test", "production"}:
            raise ValueError("ENVIRONMENT must be development, test or production")
        if self.environment == "production" and (not self.api_token or self.allow_demo_model):
            raise ValueError("Production requires API_TOKEN and ALLOW_DEMO_MODEL=false")
        if self.api_token is not None and (len(self.api_token) < 32 or not self.api_token.isascii()):
            raise ValueError("API_TOKEN must contain at least 32 ASCII characters")
        if min(self.max_csv_bytes, self.max_csv_rows, self.max_export_rows) <= 0:
            raise ValueError("Resource limits must be positive")
        if self.database_timeout <= 0 or not 1 <= self.port <= 65535:
            raise ValueError("Invalid database timeout or port")
        if self.log_level not in {"critical", "error", "warning", "info", "debug"}:
            raise ValueError("LOG_LEVEL must be critical/error/warning/info/debug")

    @classmethod
    def from_env(cls):
        production = os.getenv("ENVIRONMENT", "development") == "production"
        font = os.getenv("PDF_FONT_PATH")
        return cls(
            database_path=Path(os.getenv("DATABASE_PATH", "data/feedback.db")),
            model_path=Path(os.getenv("MODEL_PATH", "artifacts/production.joblib")),
            model_backend=os.getenv("MODEL_BACKEND", "sklearn"),
            phobert_sentiment_run=Path(os.environ["PHOBERT_SENTIMENT_RUN"]) if os.getenv("PHOBERT_SENTIMENT_RUN") else None,
            phobert_topic_run=Path(os.environ["PHOBERT_TOPIC_RUN"]) if os.getenv("PHOBERT_TOPIC_RUN") else None,
            phobert_cpu_threads=int(os.getenv("PHOBERT_CPU_THREADS", "1")),
            environment=os.getenv("ENVIRONMENT", "development"),
            cors_origins=tuple(x.strip() for x in os.getenv(
                "CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()),
            api_token=os.getenv("API_TOKEN") or None,
            allow_demo_model=flag("ALLOW_DEMO_MODEL", not production),
            auto_migrate=flag("AUTO_MIGRATE", not production),
            max_csv_bytes=int(os.getenv("MAX_CSV_BYTES", "2097152")),
            max_csv_rows=int(os.getenv("MAX_CSV_ROWS", "1000")),
            max_export_rows=int(os.getenv("MAX_EXPORT_ROWS", "5000")),
            database_timeout=float(os.getenv("DATABASE_TIMEOUT", "5")),
            pdf_font_path=Path(font) if font else None,
            host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "info"),
        )
