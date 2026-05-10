import os
import json
import asyncio
from collections import deque
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from aiokafka import AIOKafkaConsumer
import httpx
import xml.etree.ElementTree as ET

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
risk_history = deque(maxlen=1000)
cases_store = {}
txn_to_case = {}


def _to_iso(value):
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    return datetime.utcnow().isoformat()


def _parse_iso(value):
    if not value:
        return datetime.utcnow()
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


def ingest_risk_event(payload: dict):
    event = dict(payload)
    event["received_at"] = _to_iso(event.get("received_at"))
    risk_history.append(event)

    decision = str(event.get("decision", "APPROVE")).upper()
    if decision in {"REJECT", "REVIEW"}:
        txn_id = event.get("transaction_id", "unknown")
        case_id = txn_to_case.get(txn_id)
        if not case_id:
            case_id = f"CASE-{len(cases_store) + 1:04d}"
            txn_to_case[txn_id] = case_id
            cases_store[case_id] = {
                "id": case_id,
                "transactionId": txn_id,
                "accountId": event.get("account_id", "unknown"),
                "riskScore": round(float(event.get("unified_score", 0.0)) * 100, 2),
                "status": "Open",
                "created": event["received_at"],
            }
        else:
            cases_store[case_id]["riskScore"] = round(float(event.get("unified_score", 0.0)) * 100, 2)
    return event

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
                    payload = ingest_risk_event(msg.value)
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

@app.get("/api/history/recent-alerts")
async def get_recent_alerts(limit: int = 10):
    capped_limit = max(1, min(limit, 100))
    alerts = [e for e in reversed(risk_history) if str(e.get("decision", "")).upper() != "APPROVE"]
    return alerts[:capped_limit]

@app.get("/api/history/dashboard-stats")
async def get_dashboard_stats():
    events = list(risk_history)
    live_events = len(events)
    rejected_events = sum(1 for e in events if str(e.get("decision", "")).upper() == "REJECT")
    active_alerts = sum(1 for e in events if str(e.get("decision", "")).upper() != "APPROVE")
    high_risk = rejected_events

    fraud_rate = "0.00%"
    trans_min = "0.0"
    if live_events:
        newest = _parse_iso(events[-1].get("received_at"))
        oldest = _parse_iso(events[0].get("received_at"))
        elapsed_minutes = max((newest - oldest).total_seconds() / 60, 1 / 60)
        trans_min = f"{(live_events / elapsed_minutes):.1f}"
        fraud_rate = f"{((rejected_events / live_events) * 100):.2f}%"

    return {
        "fraudRate": fraud_rate,
        "activeAlerts": active_alerts,
        "transMin": trans_min,
        "highRisk": high_risk,
        "liveEvents": live_events,
        "rejectedEvents": rejected_events,
    }

@app.get("/api/cases")
async def list_cases():
    return sorted(cases_store.values(), key=lambda c: c["created"], reverse=True)

@app.patch("/api/cases/{case_id}")
async def update_case(case_id: str, payload: dict):
    case = cases_store.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    status = payload.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="Missing status")
    case["status"] = status
    return case

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
