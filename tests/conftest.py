"""Every application test owns a temporary database and deterministic predictor."""
import pytest
from fastapi.testclient import TestClient
from backend.app.database import Database
from backend.app.main import create_app
from backend.app.repository import SQLiteFeedbackRepository
from backend.app.services.feedback import FeedbackService
from backend.app.settings import Settings


class FakePredictor:
    model_version = "test-model-v1"
    is_fallback = False

    def predict(self, text):
        if "MODEL_FAILURE" in text:
            raise ValueError("private model error must not reach clients")
        return {"text": text, "sentiment_label": "positive", "sentiment_confidence": 0.8,
                "topic_label": "lecturer", "topic_confidence": 0.9,
                "model_version": self.model_version}


@pytest.fixture
def settings(tmp_path):
    return Settings(database_path=tmp_path / "feedback.db", model_path=tmp_path / "absent.joblib",
                    environment="test")


@pytest.fixture
def predictor():
    return FakePredictor()


@pytest.fixture
def repository(settings):
    database = Database(settings.database_path)
    database.initialize()
    return SQLiteFeedbackRepository(database)


@pytest.fixture
def service(repository, predictor):
    return FeedbackService(repository, predictor)


@pytest.fixture
def client(settings, predictor):
    app = create_app(settings, predictor)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
