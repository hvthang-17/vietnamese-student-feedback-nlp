from fastapi import APIRouter, Depends, HTTPException, Path, Query
from ..domain.models import FeedbackFilter
from ..schemas import DashboardSummary, FeedbackPage, FeedbackRecord
from ..services.feedback import FeedbackService
from .dependencies import get_feedback, get_filters

router = APIRouter(tags=["feedback"])


@router.get("/feedback", response_model=FeedbackPage)
def feedback(filters: FeedbackFilter = Depends(get_filters),
             page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
             service: FeedbackService = Depends(get_feedback)):
    return service.feedback(filters, page, page_size)


@router.get("/feedback/{feedback_id}", response_model=FeedbackRecord)
def feedback_detail(feedback_id: int = Path(ge=1), service: FeedbackService = Depends(get_feedback)):
    row = service.get(feedback_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy phản hồi.")
    return row


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard(filters: FeedbackFilter = Depends(get_filters),
              service: FeedbackService = Depends(get_feedback)):
    return service.summary(filters)
