import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from aiokafka import AIOKafkaConsumer
import httpx
import xml.etree.ElementTree as ET
from pydantic import BaseModel
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.database import get_db
from app.models import RiskScoreRecord, Case

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8004")
GRAPH_SERVICE_URL = os.getenv("GRAPH_SERVICE_URL", "http://localhost:8002")

app = FastAPI(title="Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = set()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_risk_scores())

async def consume_risk_scores():
    while True:
        try:
            consumer = AIOKafkaConsumer(
                "risk-scores",
                bootstrap_servers=KAFKA_BROKERS,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset="latest"
            )
            await consumer.start()
            try:
                async for msg in consumer:
                    payload = msg.value
                    for ws in list(clients):
                        try:
                            await ws.send_json(payload)
                        except Exception:
                            if ws in clients:
                                clients.remove(ws)
            finally:
                await consumer.stop()
        except Exception as e:
            print(f"Failed to start dashboard kafka consumer: {e}. Retrying in 3s...")
            await asyncio.sleep(3)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

# --- Database Persistence REST Endpoints ---

class CaseUpdate(BaseModel):
    status: str

@app.get("/api/recent-alerts")
async def get_recent_alerts(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Return most recent flagged items for pre-seeding the dashboard dashboard"""
    result = await db.execute(
        select(RiskScoreRecord)
        .where(RiskScoreRecord.decision.in_(["REJECT", "REVIEW"]))
        .order_by(desc(RiskScoreRecord.created_at))
        .limit(limit)
    )
    records = result.scalars().all()
    # Transform to match formatting expected by Dashboard.tsx
    return [{
        "transaction_id": r.transaction_id,
        "unified_score": r.unified_score,
        "decision": r.decision
    } for r in records]

@app.get("/api/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Compute cumulative stats for hydration"""
    total_result = await db.execute(select(func.count(RiskScoreRecord.transaction_id)))
    total = total_result.scalar() or 0

    reject_result = await db.execute(
        select(func.count(RiskScoreRecord.transaction_id))
        .where(RiskScoreRecord.decision == "REJECT")
    )
    rejects = reject_result.scalar() or 0

    alerts_result = await db.execute(
        select(func.count(RiskScoreRecord.transaction_id))
        .where(RiskScoreRecord.decision.in_(["REJECT", "REVIEW"]))
    )
    alerts = alerts_result.scalar() or 0

    fraud_pct = (rejects / total * 100) if total > 0 else 0

    return {
        "fraudRate": f"{fraud_pct:.2f}%",
        "activeAlerts": alerts,
        "highRisk": rejects,
        "liveEvents": total,
        "rejectedEvents": rejects,
        "transMin": "N/A" 
    }

@app.get("/api/cases")
async def list_cases(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Returns the persistent cases for human review"""
    result = await db.execute(
        select(Case)
        .order_by(desc(Case.created_at))
        .limit(limit)
    )
    cases = result.scalars().all()
    return [c.to_dict() for c in cases]

@app.patch("/api/cases/{case_id}")
async def update_case(case_id: str, payload: CaseUpdate, db: AsyncSession = Depends(get_db)):
    """Update a case (Assign investigation, resolve, etc)"""
    result = await db.execute(select(Case).where(Case.id == case_id))
    record = result.scalar_one_or_none()
    if not record:
         raise HTTPException(status_code=404, detail="Case not found")
    record.status = payload.status
    await db.commit()
    await db.refresh(record)
    return record.to_dict()

@app.post("/api/explain")
async def explain_transaction(payload: dict):
    # Proxy to llm-service
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{LLM_SERVICE_URL}/explain", json=payload, timeout=30.0)
            return resp.json()
        except Exception as e:
            return {"error": str(e), "explanation": "Unable to reach LLM service."}

@app.get("/api/graph/{account_id}")
async def get_graph(account_id: str):
    # Proxy to graph-service
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{GRAPH_SERVICE_URL}/graph/{account_id}", timeout=10.0)
            return resp.json()
        except Exception as e:
            return {"error": str(e), "nodes": [], "edges": []}

@app.get("/api/str/{case_id}")
async def generate_str_xml(case_id: str):
    root = ET.Element("SuspiciousTransactionReport")
    fiu_header = ET.SubElement(root, "ReportHeader")
    ET.SubElement(fiu_header, "ReportFormatCode").text = "ARF1.0"
    ET.SubElement(fiu_header, "ReportType").text = "SuspiciousTransaction"
    
    case_details = ET.SubElement(root, "CaseDetails")
    ET.SubElement(case_details, "CaseID").text = case_id
    ET.SubElement(case_details, "Status").text = "N"
    ET.SubElement(case_details, "SuspicionDetails").text = "Generated by FundGuard Risk Engine. Awaiting analyst review."
    
    # Normally we would fetch the case details from the database here
    
    xml_str = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="STR_{case_id}.xml"'}
    )
