from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from .db import ensure_seeded
from .routers import courses, enrollments, me, professors, students

app = FastAPI(title="Course Registration API")


@app.on_event("startup")
def on_startup() -> None:
    duration = ensure_seeded()
    app.state.seed_duration = duration
    app.state.data_ready = True


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail), "details": {}}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            }
        },
    )


@app.get("/health", response_model=None)
def health(request: Request):
    if not getattr(request.app.state, "data_ready", False):
        return JSONResponse(status_code=503, content={"status": "starting"})
    return {"status": "ok"}


app.include_router(students.router)
app.include_router(professors.router)
app.include_router(courses.router)
app.include_router(me.router)
app.include_router(enrollments.router)
