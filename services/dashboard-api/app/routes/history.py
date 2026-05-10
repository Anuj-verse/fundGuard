from fastapi import APIRouter, Depends
from sqlalchemy import select, desc, func, text, case
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import RiskScoreRecord

router = APIRouter()


@router.get("/api/recent-alerts")
async def get_recent_alerts(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RiskScoreRecord)
        .where(RiskScoreRecord.alert_level.in_(["HIGH", "CRITICAL"]))
        .order_by(desc(RiskScoreRecord.created_at))
        .limit(limit)
    )
    records = result.scalars().all()
    return [r.to_dict() for r in records]


@router.get("/api/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    stmt = select(
        func.count().label("total_today"),
        func.avg(RiskScoreRecord.final_score).label("avg_score"),
        func.sum(case((RiskScoreRecord.alert_level.in_(["HIGH", "CRITICAL"]), 1), else_=0)).label("alerts_today")
    ).where(text("created_at >= datetime('now','-24 hours')"))
    row = await db.execute(stmt)
    row = row.one_or_none()
    if not row:
        return {"total_today": 0, "alerts_today": 0, "fraud_rate": 0, "avg_risk_score": 0}
    total = row.total_today or 0
    alerts = row.alerts_today or 0
    return {
        "total_today": int(total),
        "alerts_today": int(alerts),
        "fraud_rate": round((alerts / total * 100), 2) if total > 0 else 0,
        "avg_risk_score": round(row.avg_score or 0, 1),
    }
