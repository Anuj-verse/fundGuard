from pydantic import BaseModel, Field
from datetime import datetime

class TransactionRequest(BaseModel):
    transaction_id: str
    timestamp: datetime
    sender_account_id: str
    receiver_account_id: str
    amount: float
    currency: str = "INR"
    channel: str
    sender_geo_latitude: float | None = None
    sender_geo_longitude: float | None = None
    receiver_geo_latitude: float | None = None
    receiver_geo_longitude: float | None = None
    sender_geo_state: str | None = None
    receiver_geo_state: str | None = None
    # For a real implementation, we would probably pull velocities from Redis,
    # but based on the plan, we might accept them or mock them. Let's include them as optional.
    sender_velocity_1h: int | None = None
    sender_velocity_24h: int | None = None
    receiver_velocity_1h: int | None = None
    amount_vs_avg_ratio: float | None = None
    is_new_account: int | None = None
    device_change_flag: int | None = None
    beneficiary_risk_score: float | None = None
    account_age_days: int | None = None

class ScoreResponse(BaseModel):
    transaction_id: str
    anomaly_score: float
    decision: str
    latency_ms: float
    features_used: dict[str, float]
