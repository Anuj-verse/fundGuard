import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from aiokafka import AIOKafkaConsumer
import httpx

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8004")

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
                t_id = payload.get("transaction_id")
                score = payload.get("unified_score")
                for ws in list(clients):
                    try:
                        await ws.send_json(payload)
                    except Exception:
                        clients.remove(ws)
        finally:
            await consumer.stop()
    except Exception as e:
        print(f"Failed to start dashboard kafka consumer: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

@app.post("/api/explain")
async def explain_transaction(payload: dict):
    # Proxy to llm-service
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{LLM_SERVICE_URL}/explain", json=payload, timeout=30.0)
            return resp.json()
        except Exception as e:
            return {"error": str(e), "explanation": "Unable to reach LLM service."}
