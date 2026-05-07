from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class TransactionRequest(BaseModel):
    transaction_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender_account_id: str
    receiver_account_id: str
    amount: float
    currency: str = "INR"
    channel: str = "WEB"
    sender_geo_latitude: Optional[float] = None
    sender_geo_longitude: Optional[float] = None
    receiver_geo_latitude: Optional[float] = None
    receiver_geo_longitude: Optional[float] = None
    sender_geo_state: Optional[str] = None
    receiver_geo_state: Optional[str] = None
    # Features retrieved from Redis in edge-service
    sender_velocity_1h: Optional[int] = 0
    sender_velocity_24h: Optional[int] = 0
    receiver_velocity_1h: Optional[int] = 0
    amount_vs_avg_ratio: Optional[float] = 1.0
    is_new_account: Optional[int] = 0
    device_change_flag: Optional[int] = 0
    beneficiary_risk_score: Optional[float] = 0.0
    account_age_days: Optional[int] = 0

class TransactionLiveEvent(BaseModel):
    """Published to Kafka 'transactions-live' by edge-service"""
    transaction: TransactionRequest
    edge_score: float
    edge_decision: str
    latency_ms: float

class GraphEvent(BaseModel):
    """Published to Kafka 'graph-events' by graph-service"""
    transaction_id: str
    sender_account_id: str
    receiver_account_id: str
    graph_risk_score: float
    graph_flags: List[str]
    graph_subnetwork: Dict[str, Any]

class RiskScoreEvent(BaseModel):
    """Published to Kafka 'risk-scores' by risk-engine"""
    transaction_id: str
    sender_account_id: str
    unified_risk_score: float
    decision: str
    edge_score: float
    graph_score: float
    rules_triggered: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transactions: List[str] = Field(default_factory=list)
    graph_subnetwork: Dict[str, Any] = Field(default_factory=dict)
