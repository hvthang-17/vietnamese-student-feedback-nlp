"""HTTP-to-application composition; no model or database globals."""
import hmac
from fastapi import Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import AwareDatetime

from ..domain.models import FeedbackFilter, Sentiment, Topic
from ..services.feedback import FeedbackService

bearer = HTTPBearer(auto_error=False)


def authorize(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    token = request.app.state.settings.api_token
    if token is None:
        return
    supplied = credentials.credentials if credentials else ""
    if not hmac.compare_digest(supplied.encode("utf-8"), token.encode("utf-8")):
        raise HTTPException(401, "Thông tin xác thực không hợp lệ.", headers={"WWW-Authenticate": "Bearer"})


def get_feedback(request: Request) -> FeedbackService:
    return request.app.state.feedback


def get_filters(
    sentiment: Sentiment | None = Query(None), topic: Topic | None = Query(None),
    predicted_from: AwareDatetime | None = Query(None),
    predicted_to: AwareDatetime | None = Query(None),
) -> FeedbackFilter:
    try:
        return FeedbackFilter(sentiment, topic, predicted_from, predicted_to)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
