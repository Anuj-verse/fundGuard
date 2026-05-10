import os
import time
import json
import threading
from kafka import KafkaProducer, KafkaConsumer
import asyncio
from app.database import engine, async_session
from app.models import Base, RiskScoreRecord, Case
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.schemas import TransactionRequest
from app.redis_client import redis_client

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
                    # Persist to DB
                    try:
                        async def persist():
                            async with async_session() as session:
                                record = RiskScoreRecord(
                                    txn_id=txn_id,
                                    sender_account=txn_dict.get("sender_account_id"),
                                    receiver_account=txn_dict.get("receiver_account_id"),
                                    amount=float(txn_dict.get("amount", 0)),
                                    final_score=unified_score,
                                    edge_score=edge_score,
                                    graph_score=graph_score,
                                    alert_level=("HIGH" if unified_score > 0.8 else ("MEDIUM" if unified_score > 0.5 else "LOW")),
                                    patterns=graph_flags,
                                    graph_features={},
                                    decision=decision,
                                )
                                session.add(record)
                                await session.commit()

                                # Auto-create case for high alerts
                                if record.alert_level in ("HIGH", "CRITICAL"):
                                    existing = await session.get(Case, record.txn_id)
                                    if not existing:
                                        case = Case(
                                            txn_id=record.txn_id,
                                            sender_account=record.sender_account,
                                            final_score=record.final_score,
                                            alert_level=record.alert_level,
                                            patterns=record.patterns,
                                        )
                                        session.add(case)
                                        await session.commit()

                        asyncio.run(persist())
                    except Exception as e:
                        print(f"Warning: failed to persist risk record: {e}")

                    active_producer = get_or_create_producer()
                    if active_producer:
                        print(f"Publishing risk score for txn {txn_id}")
                        active_producer.send("risk-scores", value=response)
                        active_producer.flush(timeout=0.1)
                except Exception as e:
                    print(f"Error processing graph-events message: {e}")

            consumer.close()
        except Exception as e:
            print(f"Risk-engine consumer connection failed: {e}. Retrying in 3s...")
            time.sleep(3)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer, consumer_thread, running
    running = True
    # Ensure DB tables exist
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("Risk-engine DB tables ensured")
    except Exception as e:
        print(f"Warning: could not create DB tables: {e}")

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