import os
import json
import asyncio
import sqlite3
import threading
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from aiokafka import AIOKafkaConsumer
import httpx
import xml.etree.ElementTree as ET

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8004")
GRAPH_SERVICE_URL = os.getenv("GRAPH_SERVICE_URL", "http://localhost:8002")
DB_PATH = os.getenv("DASHBOARD_DB_PATH", "/tmp/fundguard_dashboard.db")

app = FastAPI(title="Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = set()
db_lock = threading.Lock()


def _db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db_lock:
        conn = _db_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS risk_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT NOT NULL,
                    unified_score REAL NOT NULL,
                    decision TEXT NOT NULL,
                    edge_score REAL NOT NULL DEFAULT 0.0,
                    graph_score REAL NOT NULL DEFAULT 0.0,
                    rule_score REAL NOT NULL DEFAULT 0.0,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cases (
                    id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()


def persist_risk_score(payload: dict):
    txn_id = payload.get("transaction_id") or f"TXN-{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}"
    decision = str(payload.get("decision") or "APPROVE")
    unified_score = float(payload.get("unified_score") or 0.0)
    components = payload.get("components") or {}
    edge_score = float(components.get("edge_score") or 0.0)
    graph_score = float(components.get("graph_score") or 0.0)
    rule_score = float(components.get("rule_score") or 0.0)
    created_at = datetime.now(tz=timezone.utc).isoformat()

    with db_lock:
        conn = _db_connection()
        try:
            conn.execute(
                """
                INSERT INTO risk_scores (
                    transaction_id, unified_score, decision, edge_score, graph_score, rule_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (txn_id, unified_score, decision, edge_score, graph_score, rule_score, created_at),
            )
            if decision != "APPROVE":
                case_id = f"CASE-{txn_id}"
                conn.execute(
                    """
                    INSERT OR IGNORE INTO cases (id, transaction_id, risk_score, status, created_at)
                    VALUES (?, ?, ?, 'Open', ?)
                    """,
                    (case_id, txn_id, unified_score * 100, created_at),
                )
            conn.commit()
        finally:
            conn.close()

@app.on_event("startup")
async def startup_event():
    init_db()
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
                    persist_risk_score(payload)
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


@app.get("/api/recent-alerts")
async def recent_alerts(limit: int = 20):
    with db_lock:
        conn = _db_connection()
        try:
            rows = conn.execute(
                """
                SELECT transaction_id, unified_score, decision, created_at
                FROM risk_scores
                WHERE decision != 'APPROVE'
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (max(1, min(limit, 200)),),
            ).fetchall()
        finally:
            conn.close()
    return [dict(row) for row in rows]


@app.get("/api/stats")
async def dashboard_stats():
    with db_lock:
        conn = _db_connection()
        try:
            total = conn.execute("SELECT COUNT(*) FROM risk_scores").fetchone()[0]
            rejected = conn.execute("SELECT COUNT(*) FROM risk_scores WHERE decision = 'REJECT'").fetchone()[0]
            alerts = conn.execute("SELECT COUNT(*) FROM risk_scores WHERE decision != 'APPROVE'").fetchone()[0]
            first_ts = conn.execute("SELECT created_at FROM risk_scores ORDER BY created_at ASC LIMIT 1").fetchone()
        finally:
            conn.close()

    if first_ts:
        started = datetime.fromisoformat(first_ts[0])
        elapsed_minutes = max((datetime.now(tz=timezone.utc) - started).total_seconds() / 60.0, 1 / 60)
    else:
        elapsed_minutes = 1 / 60

    return {
        "fraudRate": f"{((rejected / total) * 100 if total else 0.0):.2f}%",
        "activeAlerts": alerts,
        "transMin": f"{(total / elapsed_minutes if total else 0.0):.1f}",
        "highRisk": rejected,
        "liveEvents": total,
        "rejectedEvents": rejected,
    }


@app.get("/api/cases")
async def list_cases(limit: int = 100):
    with db_lock:
        conn = _db_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, transaction_id, risk_score, status, created_at
                FROM cases
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (max(1, min(limit, 500)),),
            ).fetchall()
        finally:
            conn.close()
    return [dict(row) for row in rows]

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
