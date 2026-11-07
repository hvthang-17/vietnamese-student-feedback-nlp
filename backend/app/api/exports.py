from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from ..clock import now
from ..domain.models import FeedbackFilter
from .dependencies import get_filters

router = APIRouter(tags=["exports"])


def attachment(content: bytes, extension: str, media_type: str):
    name = f"phan-hoi-{now().strftime('%Y%m%d-%H%M%S')}.{extension}"
    return Response(content, media_type=media_type,
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/exports/csv", response_class=Response, responses={
    200: {"content": {"text/csv": {"schema": {"type": "string", "format": "binary"}}}},
    413: {"description": "Export limit exceeded"}})
def export_csv(request: Request, filters: FeedbackFilter = Depends(get_filters)):
    return attachment(request.app.state.reports.csv(filters), "csv", "text/csv; charset=utf-8")


@router.get("/exports/pdf", response_class=Response, responses={
    200: {"content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}},
    413: {"description": "Export limit exceeded"},
    503: {"description": "Unicode PDF font unavailable"}})
def export_pdf(request: Request, filters: FeedbackFilter = Depends(get_filters)):
    return attachment(request.app.state.reports.pdf(filters), "pdf", "application/pdf")
