from fastapi import APIRouter, Depends
from ..domain.models import Source
from ..schemas import BatchPredictionRequest, PredictionRequest, PredictionResponse
from ..services.feedback import FeedbackService
from .dependencies import get_feedback

router = APIRouter(tags=["predictions"])


@router.post("/predictions", response_model=PredictionResponse)
def prediction(payload: PredictionRequest, service: FeedbackService = Depends(get_feedback)):
    return service.predict(payload.text, payload.created_at)


@router.post("/predictions/batch", response_model=list[PredictionResponse])
def batch_prediction(payload: BatchPredictionRequest, service: FeedbackService = Depends(get_feedback)):
    return service.predict_many([(item.text, item.created_at) for item in payload.items], Source.BATCH)
