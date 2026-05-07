import os
import time
import json
import httpx
from kafka import KafkaProducer
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from app.schemas import IncomingTransaction, UnifiedRiskResponse
from app.redis_client import get_and_update_velocity, redis_client

EDGE_SERVICE_URL = os.getenv("EDGE_SERVICE_URL", "http://localhost:8001")
GRAPH_SERVICE_URL = os.getenv("GRAPH_SERVICE_URL", "http://localhost:8002")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")

producer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except Exception as e:
        print(f"Warning: Could not connect to Kafka. {e}")
    yield
    if producer:
        producer.close()
    await redis_client.close()

app = FastAPI(title="FundGuard Unified Risk Engine", lifespan=lifespan)

httpx_client = httpx.AsyncClient(timeout=2.0)

def apply_static_rules(txn: IncomingTransaction, features: dict) -> dict:
    rules_triggered = []
    risk_increment = 0.0
    
    if txn.amount > 500000:
        rules_triggered.append("HIGH_AMOUNT_THRESHOLD")
        risk_increment += 0.2
        
    if features.get("sender_velocity_1h", 0) > 10:
        rules_triggered.append("HIGH_VELOCITY_1H")
        risk_increment += 0.3
        
    if features.get("sender_velocity_24h", 0) > 50:
        rules_triggered.append("HIGH_VELOCITY_24H")
        risk_increment += 0.4
        
    if features.get("amount_vs_avg_ratio", 1.0) > 10.0:
        rules_triggered.append("AMOUNT_SPIKE_10X")
        risk_increment += 0.25
        
    return {
        "rules_triggered": rules_triggered,
        "rule_risk_score": min(risk_increment, 1.0)
    }

async def call_edge_service(payload: dict) -> dict:
    try:
        resp = await httpx_client.post(f"{EDGE_SERVICE_URL}/score", json=payload)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Edge service call failed: {e}")
        return {"anomaly_score": 0.0, "decision": "APPROVE"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "services": {"edge": EDGE_SERVICE_URL, "graph": GRAPH_SERVICE_URL}}

@app.post("/evaluate", response_model=UnifiedRiskResponse)
async def evaluate_transaction(txn: IncomingTransaction):
    start_time = time.time()
    
    # 1. Fetch & Update Redis Features
    redis_features = await get_and_update_velocity(txn.sender_account_id, txn.amount)
    
    # 2. Static Rules Engine
    rule_results = apply_static_rules(txn, redis_features)
    
    # 3. Call Edge Service (ONNX)
    edge_payload = txn.model_dump(mode='json')
    edge_payload.update(redis_features)
    edge_result = await call_edge_service(edge_payload)
    
    # 4. Integrate Graph signals (Simulated sync call, normally async or cached)
    # We will simply check if the sender is in a known fraud ring by pinging the active patterns
    graph_risk_score = 0.0
    graph_flags = []
    try:
        graph_resp = await httpx_client.get(f"{GRAPH_SERVICE_URL}/graph/{txn.sender_account_id}?depth=1")
        if graph_resp.status_code == 200:
             # Basic heuristic: if network is flagged, increase risk
             g_data = graph_resp.json()
             if any(n.get("risk_score", 0) > 0.8 for n in g_data.get("nodes", [])):
                 graph_risk_score = 0.5
                 graph_flags.append("ASSOCIATED_WITH_HIGH_RISK_NODE")
    except Exception as e:
        print(f"Graph service call failed: {e}")

    # 5. Unify Scores (Weighted average or hard logic)
    rule_score = rule_results["rule_risk_score"]
    edge_score = edge_result.get("anomaly_score", 0.0)
    
    unified_score = (rule_score * 0.3) + (edge_score * 0.5) + (graph_risk_score * 0.2)
    unified_score = min(unified_score, 1.0)
    
    # 6. Decision Logic
    decision = "APPROVE"
    if unified_score > 0.8 or "REJECT" in edge_result.get("decision", "") or len(rule_results["rules_triggered"]) >= 3:
        decision = "REJECT"
    elif unified_score > 0.6:
        decision = "REVIEW"
        
    latency_ms = (time.time() - start_time) * 1000
    
    response = UnifiedRiskResponse(
        transaction_id=txn.transaction_id,
        unified_risk_score=unified_score,
        decision=decision,
        latency_ms=latency_ms,
        components={
            "rules": {"score": rule_score, "triggered": rule_results["rules_triggered"]},
            "edge": {"score": edge_score, "decision": edge_result.get("decision")},
            "graph": {"score": graph_risk_score, "flags": graph_flags},
            "redis_features": redis_features
        },
        triggered_rules=rule_results["rules_triggered"] + graph_flags
    )
    
    # 7. Emit to Kafka for Dashboard/Alerts
    if producer and decision in ["REVIEW", "REJECT"]:
        try:
            producer.send("risk-alerts", value=response.model_dump())
        except Exception as e:
            print(f"Failed to publish to Kafka: {e}")
            
    return response