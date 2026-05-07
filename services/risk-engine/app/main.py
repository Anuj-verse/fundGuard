import os
import time
import json
import threading
from kafka import KafkaProducer, KafkaConsumer
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.schemas import TransactionRequest
from app.redis_client import redis_client

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")

producer = None
consumer_thread = None
running = False

def consume_graph_events():
    consumer = KafkaConsumer(
        "graph-events",
        bootstrap_servers=KAFKA_BROKERS,
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        auto_offset_reset='latest'
    )
    for msg in consumer:
        if not running:
            break
        try:
            event = msg.value
            txn_dict = event.get("transaction", {})
            txn_id = event.get("transaction_id", "unknown")
            edge_score = float(event.get("edge_score", 0.0))
            graph_score = float(event.get("graph_risk_score", 0.0))
            graph_flags = event.get("graph_flags", [])

            # Simple static rule simulation on unwrapped payload
            amount = float(txn_dict.get("amount", 0))
            rule_score = 0.2 if amount > 500000 else 0.0
            triggered = ["HIGH_AMOUNT"] if amount > 500000 else []

            unified_score = (rule_score * 0.2) + (edge_score * 0.5) + (graph_score * 0.3)
            unified_score = min(unified_score, 1.0)
            
            decision = "APPROVE"
            if unified_score > 0.8:
                decision = "REJECT"
            elif unified_score > 0.5:
                decision = "REVIEW"

            response = {
                "transaction_id": txn_id,
                "unified_score": unified_score,
                "decision": decision,
                "components": {
                    "edge_score": edge_score,
                    "graph_score": graph_score,
                    "rule_score": rule_score,
                    "graph_flags": graph_flags
                }
            }
            if producer:
                print(f"Publishing risk score for txn {txn_id}")
                producer.send("risk-scores", value=response)
                producer.flush(timeout=0.1)
        except Exception as e:
            print(f"Error processing graph-events message: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer, consumer_thread, running
    running = True
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        consumer_thread = threading.Thread(target=consume_graph_events, daemon=True)
        consumer_thread.start()
    except Exception as e:
        print(f"Warning: Could not connect to Kafka. {e}")
    yield
    running = False
    if producer:
        producer.close()
    await redis_client.close()

app = FastAPI(title="FundGuard Unified Risk Engine", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "ok", "consumer_active": consumer_thread.is_alive() if consumer_thread else False}
            
    return response