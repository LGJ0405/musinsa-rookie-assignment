from __future__ import annotations

import sqlite3
from fastapi import APIRouter, Depends

from ..db import get_db
from ..schemas import ProfessorOut

router = APIRouter(prefix="/professors", tags=["professors"])


@router.get("", response_model=list[ProfessorOut])
def list_professors(db: sqlite3.Connection = Depends(get_db)) -> list[ProfessorOut]:
    rows = db.execute(
        """
        SELECT p.id, p.name, p.department_id, d.name AS department_name
        FROM professors p
        JOIN departments d ON d.id = p.department_id
        ORDER BY p.id
        """
    ).fetchall()
    return [ProfessorOut(**dict(row)) for row in rows]
