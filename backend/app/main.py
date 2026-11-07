"""Application factory and ASGI entry point; no import-time model/database I/O."""
import logging
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import dashboard, exports, imports, predictions
from .api.dependencies import authorize
from .api.middleware import BodyLimitMiddleware
from .database import Database
from .domain.models import InputError, ReportUnavailableError, ResourceLimitError
from .domain.ports import Predictor
from .repository import SQLiteFeedbackRepository
from .schemas import ErrorResponse, HealthResponse
from .services.feedback import FeedbackService
from .services.imports import ImportService
from .services.reports import ReportService
from .settings import Settings

logger = logging.getLogger("feedback.api")


def create_app(settings: Settings | None = None, predictor: Predictor | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        logger.setLevel(settings.log_level.upper())
        if not logger.handlers and not logging.getLogger().handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
            logger.addHandler(handler)
        from .inference import load_predictor
        model = predictor if predictor is not None else load_predictor(settings)
        if model.is_fallback and not settings.allow_demo_model:
            raise RuntimeError("Demo predictor is not permitted in this environment")
        database = Database(settings.database_path, settings.database_timeout)
        if settings.auto_migrate:
            database.initialize()
        database.verify_schema()
        repository = SQLiteFeedbackRepository(database)
        feedback = FeedbackService(repository, model)
        application.state.database = database
        application.state.feedback = feedback
        application.state.imports = ImportService(feedback, settings)
        application.state.reports = ReportService(repository, settings)
        try:
            yield
        finally:
            # Release process-level model references; connections are operation-scoped.
            del application.state.feedback
            del application.state.imports
            del application.state.reports

    application = FastAPI(title="Student Feedback NLP API", version="1.1.0", lifespan=lifespan)
    application.state.settings = settings
    application.add_middleware(BodyLimitMiddleware, limit=settings.max_csv_bytes + 65536)
    application.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins),
                               allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Authorization"],
                               expose_headers=["X-Request-ID", "Content-Disposition"])

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request.state.request_id
            return response
        except Exception as exc:
            # Handle before ServerErrorMiddleware re-raises into Uvicorn's traceback logger.
            logger.error("request_id=%s error_type=%s", request.state.request_id, type(exc).__name__)
            return JSONResponse({"detail": "Không thể xử lý yêu cầu."}, status_code=500,
                                headers={"X-Request-ID": request.state.request_id})
        finally:
            logger.info("request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
                        request.state.request_id, request.method,
                        getattr(request.scope.get("route"), "path", "<unmatched>"), status,
                        (time.perf_counter() - start) * 1000)

    def error(request: Request, code: int, detail):
        return JSONResponse({"detail": detail}, status_code=code,
                            headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")})

    @application.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        # Do not echo text/token values in validation responses.
        detail = [{key: item[key] for key in ("type", "loc", "msg") if key in item} for item in exc.errors()]
        return error(request, 422, detail)

    @application.exception_handler(ResourceLimitError)
    async def resource_limit(request: Request, exc: ResourceLimitError):
        return error(request, 413, str(exc))

    @application.exception_handler(ReportUnavailableError)
    async def unavailable_report(request: Request, exc: ReportUnavailableError):
        return error(request, 503, str(exc))

    @application.exception_handler(InputError)
    async def invalid_value(request: Request, exc: InputError):
        return error(request, 422, str(exc))

    @application.exception_handler(sqlite3.OperationalError)
    async def database_error(request: Request, exc: sqlite3.OperationalError):
        if "locked" in str(exc).lower():
            return error(request, 503, "Cơ sở dữ liệu đang bận; vui lòng thử lại.")
        return error(request, 500, "Không thể xử lý yêu cầu.")

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error("request_id=%s error_type=%s", getattr(request.state, "request_id", "unknown"), type(exc).__name__)
        return error(request, 500, "Không thể xử lý yêu cầu.")

    @application.get("/health", response_model=HealthResponse, tags=["operations"])
    def health(request: Request):
        model = request.app.state.feedback.predictor
        return {"status": "ok", "model_version": model.model_version, "fallback_model": model.is_fallback}

    @application.get("/ready", tags=["operations"])
    def ready(request: Request):
        if not request.app.state.database.ping():
            return error(request, 503, "Cơ sở dữ liệu chưa sẵn sàng.")
        return {"status": "ready"}

    api = APIRouter(prefix="/api/v1", dependencies=[Depends(authorize)], responses={
        401: {"model": ErrorResponse, "description": "Bearer credential missing or invalid when API_TOKEN is configured"},
        413: {"model": ErrorResponse, "description": "Configured resource limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal error; details are redacted"},
        503: {"model": ErrorResponse, "description": "Dependency busy or unavailable"},
    })
    for router in (predictions.router, imports.router, dashboard.router, exports.router):
        api.include_router(router)
    application.include_router(api)
    return application


app = create_app()
