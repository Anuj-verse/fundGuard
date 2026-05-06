import time
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.schemas import TransactionRequest, ScoreResponse
from app.features import FeatureExtractor
from app.scorer import OnnxScorer
from app.kafka import KafkaPublisher
from app.metrics import REQUEST_COUNT, LATENCY_HISTOGRAM

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

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": scorer is not None}

@app.get("/metrics")
def get_metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/score", response_model=ScoreResponse)
async def score_transaction(req: TransactionRequest):
    if not scorer:
        raise HTTPException(status_code=503, detail="Model not loaded")
        
    start_time = time.time()
    
    try:
        # Extract features
        features = feature_extractor.extract(req)
        
        # Run inference
        anomaly_score, decision = scorer.score(features)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Record metrics
        REQUEST_COUNT.labels(decision=decision).inc()
        LATENCY_HISTOGRAM.observe(latency_ms / 1000.0)
        
        # Prepare response
        feature_names = [
            "amount", "log_amount", "hour_of_day", "day_of_week", "is_weekend",
            "channel_encoded", "sender_velocity_1h", "sender_velocity_24h",
            "receiver_velocity_1h", "amount_vs_avg_ratio", "is_new_account",
            "device_change_flag", "geo_distance_km", "is_international",
            "structuring_flag", "round_amount_flag", "beneficiary_risk_score",
            "account_age_days"
        ]
        
        # In python >= 3.10 we can use zip and dict
        features_dict = dict(zip(feature_names, features[0].tolist()))
        
        resp = ScoreResponse(
            transaction_id=req.transaction_id,
            anomaly_score=anomaly_score,
            decision=decision,
            latency_ms=latency_ms,
            features_used=features_dict
        )
        
        # Publish to Kafka
        kafka_publisher.publish(resp.model_dump())
        
        return resp
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
