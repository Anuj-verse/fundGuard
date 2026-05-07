import time
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.schemas import TransactionRequest, TransactionLiveEvent
from app.features import FeatureExtractor
from app.scorer import OnnxScorer
from app.kafka import KafkaPublisher
from app.metrics import REQUEST_COUNT, LATENCY_HISTOGRAM
from app.redis_client import get_and_update_velocity, redis_client

app = FastAPI(title="FundGuard Edge Service")

# Global instances
feature_extractor = None
scorer = None
kafka_publisher = None

@app.on_event("startup")
async def startup_event():
    global feature_extractor, scorer, kafka_publisher
    
    feature_extractor = FeatureExtractor()
    
    model_path = os.getenv("MODEL_PATH", "models/xgboost_model.onnx")
    try:
        scorer = OnnxScorer(model_path)
    except Exception as e:
        print(f"Warning: Could not load ONNX model at {model_path}. Error: {e}")
        scorer = None
        
    kafka_brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")
    kafka_publisher = KafkaPublisher(bootstrap_servers=kafka_brokers)

@app.on_event("shutdown")
async def shutdown_event():
    if kafka_publisher:
        kafka_publisher.shutdown()
    await redis_client.close()

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": scorer is not None}

@app.get("/metrics")
def get_metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/score")
async def score_transaction(req: TransactionRequest):
    if not scorer:
        raise HTTPException(status_code=503, detail="Model not loaded")
        
    start_time = time.time()
    
    try:
        # Fetch & Update Redis Features
        redis_features = await get_and_update_velocity(req.sender_account_id, req.amount)
        req.sender_velocity_1h = redis_features["sender_velocity_1h"]
        req.sender_velocity_24h = redis_features["sender_velocity_24h"]
        req.amount_vs_avg_ratio = redis_features["amount_vs_avg_ratio"]

        # Extract features
        features = feature_extractor.extract(req)
        
        # Run inference
        anomaly_score, decision = scorer.score(features)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Record metrics
        REQUEST_COUNT.labels(decision=decision).inc()
        LATENCY_HISTOGRAM.observe(latency_ms / 1000.0)
        
        # Prepare live event
        live_event = TransactionLiveEvent(
            transaction=req,
            edge_score=anomaly_score,
            edge_decision=decision,
            latency_ms=latency_ms
        )
        
        # Publish to Kafka properly
        kafka_publisher.publish(live_event.model_dump(mode='json'))
        
        return {
            "transaction_id": req.transaction_id,
            "anomaly_score": anomaly_score,
            "decision": decision,
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
