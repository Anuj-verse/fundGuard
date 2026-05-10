from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import Case
from pydantic import BaseModel

router = APIRouter(prefix="/api/cases")

class CaseUpdateRequest(BaseModel):
    status: str | None = None
    assigned_to: str | None = None


@router.get("/")
async def list_cases(status: str | None = None, limit: int = 100, db: AsyncSession = Depends(get_db)):
    query = select(Case).order_by(desc(Case.created_at)).limit(limit)
    if status:
        query = query.where(Case.status == status)
    result = await db.execute(query)
    return [c.to_dict() for c in result.scalars().all()]


@router.get("/{case_id}")
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return case.to_dict()


@router.patch("/{case_id}")
async def update_case(case_id: str, body: CaseUpdateRequest, db: AsyncSession = Depends(get_db)):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    if body.status:
        case.status = body.status
    if body.assigned_to:
        case.assigned_to = body.assigned_to
    await db.commit()
    return case.to_dict()


@router.post("/{case_id}/approve")
async def approve_case(case_id: str, db: AsyncSession = Depends(get_db)):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    case.status = "CLOSED"
    await db.commit()
    return {"message": "Case approved (false positive)", "case_id": case_id}


@router.post("/{case_id}/reject")
async def reject_case(case_id: str, db: AsyncSession = Depends(get_db)):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    case.status = "PENDING_STR"
    await db.commit()
    return {"message": "Case flagged for STR filing", "case_id": case_id}
