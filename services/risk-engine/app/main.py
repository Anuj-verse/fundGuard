import os
import time
import json
import threading
from kafka import KafkaProducer, KafkaConsumer
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.schemas import TransactionRequest
from app.redis_client import redis_client
from app.database import SessionLocal, engine
from app.models import Base, RiskScoreRecord, Case

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")

producer = None
producer_lock = threading.Lock()
consumer_thread = None
running = False


def get_or_create_producer():
    global producer
    if producer:
        return producer

    with producer_lock:
        if producer:
            return producer
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Connected Kafka producer for risk-engine")
        except Exception as e:
            print(f"Risk-engine producer connection failed: {e}")
            producer = None
    return producer

def consume_graph_events():
    while running:
        try:
            consumer = KafkaConsumer(
                "graph-events",
                bootstrap_servers=KAFKA_BROKERS,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='latest'
            )
            print("Connected Kafka consumer for graph-events")

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
                    rule_score = 1.0 if amount > 500000 else 0.0
                    triggered = ["HIGH_AMOUNT"] if amount > 500000 else []

                    unified_score = (rule_score * 0.3) + (edge_score * 0.4) + (graph_score * 0.3)

                    # Boost score heavily if there are blatant graph flags or rule triggers
                    if triggered or graph_flags:
                        unified_score += 0.5

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

                    active_producer = get_or_create_producer()
                    if active_producer:
                        print(f"Publishing risk score for txn {txn_id}")
                        active_producer.send("risk-scores", value=response)
                        active_producer.flush(timeout=0.1)

                    # Persistence logic
                    try:
                        db = SessionLocal()
                        # 1. Record Risk Score
                        record = RiskScoreRecord(
                            transaction_id=txn_id,
                            sender_account_id=txn_dict.get("sender_account_id"),
                            receiver_account_id=txn_dict.get("receiver_account_id"),
                            amount=amount,
                            unified_score=unified_score,
                            edge_score=edge_score,
                            graph_score=graph_score,
                            rule_score=rule_score,
                            graph_flags=graph_flags,
                            decision=decision
                        )
                        db.add(record)

                        # 2. Create Case if high risk
                        if decision in ["REJECT", "REVIEW"]:
                            # Check for existing to prevent duplication
                            existing_case = db.query(Case).filter(Case.transaction_id == txn_id).first()
                            if not existing_case:
                                new_case = Case(
                                    transaction_id=txn_id,
                                    sender_account_id=txn_dict.get("sender_account_id"),
                                    unified_score=unified_score,
                                    decision=decision,
                                    status="OPEN"
                                )
                                db.add(new_case)
                        
                        db.commit()
                        db.close()
                    except Exception as db_err:
                        print(f"Database persistence error: {db_err}")
                except Exception as e:
                    print(f"Error processing graph-events message: {e}")

            consumer.close()
        except Exception as e:
            print(f"Risk-engine consumer connection failed: {e}. Retrying in 3s...")
            time.sleep(3)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer, consumer_thread, running
    
    # Auto create tables
    try:
        Base.metadata.create_all(bind=engine)
        print("Successfully created/verified database tables.")
    except Exception as e:
        print(f"Error running database migration: {e}")

    running = True
    get_or_create_producer()
    consumer_thread = threading.Thread(target=consume_graph_events, daemon=True)
    consumer_thread.start()
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