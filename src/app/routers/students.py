from __future__ import annotations

import sqlite3
from fastapi import APIRouter, Depends

from ..db import get_db
from ..schemas import StudentOut

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentOut])
def list_students(db: sqlite3.Connection = Depends(get_db)) -> list[StudentOut]:
    rows = db.execute(
        "SELECT id, name, max_credits FROM students ORDER BY id"
    ).fetchall()
    return [StudentOut(**dict(row)) for row in rows]
