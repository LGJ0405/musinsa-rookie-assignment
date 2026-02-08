from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, Header, status

from ..db import get_db
from ..errors import parse_student_id
from ..schemas import EnrollmentCreate, EnrollmentOut
from ..services.enrollment_service import cancel_enrollment, create_enrollment

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def enroll(
    payload: EnrollmentCreate,
    x_student_id: Optional[str] = Header(default=None, alias="X-Student-Id"),
    db: sqlite3.Connection = Depends(get_db),
) -> EnrollmentOut:
    student_id = parse_student_id(x_student_id)
    data = create_enrollment(db, student_id, payload.course_id)
    return EnrollmentOut(**data)


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel(
    enrollment_id: int,
    x_student_id: Optional[str] = Header(default=None, alias="X-Student-Id"),
    db: sqlite3.Connection = Depends(get_db),
) -> None:
    student_id = parse_student_id(x_student_id)
    cancel_enrollment(db, student_id, enrollment_id)
    return None
