from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException


@dataclass(frozen=True)
class AppError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict[str, Any] | None = None


def to_http_exception(error: AppError) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details or {},
            }
        },
    )


def raise_error(
    code: str, message: str, status_code: int = 400, details: dict[str, Any] | None = None
) -> None:
    raise to_http_exception(AppError(code=code, message=message, status_code=status_code, details=details))


def parse_student_id(header_value: str | None) -> int:
    if header_value is None:
        raise_error("INVALID_STUDENT_HEADER", "X-Student-Id header required", 400)
    try:
        student_id = int(header_value)
    except ValueError:
        raise_error("INVALID_STUDENT_HEADER", "X-Student-Id must be an integer", 400)
    if student_id <= 0:
        raise_error("INVALID_STUDENT_HEADER", "X-Student-Id must be positive", 400)
    return student_id
