from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from ..schemas import ImportResult

router = APIRouter(tags=["imports"])


@router.post("/imports/csv", response_model=ImportResult)
def import_csv(request: Request, file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(422, "Chỉ hỗ trợ tệp CSV.")
    limit = request.app.state.settings.max_csv_bytes
    content = file.file.read(limit + 1)
    return request.app.state.imports.import_csv(content)
