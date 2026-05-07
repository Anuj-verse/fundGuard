from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class IncomingTransaction(BaseModel):
    transaction_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender_account_id: str
    receiver_account_id: str
    amount: float
    currency: str = "INR"
    channel: str
    sender_geo_latitude: Optional[float] = None
    sender_geo_longitude: Optional[float] = None
    receiver_geo_latitude: Optional[float] = None
    receiver_geo_longitude: Optional[float] = None
    is_new_account: Optional[int] = 0
    device_change_flag: Optional[int] = 0

class UnifiedRiskResponse(BaseModel):
    transaction_id: str
    unified_risk_score: float
    decision: str  # "APPROVE", "REVIEW", "REJECT"
    latency_ms: float
    components: Dict[str, Any]  # Details from rules, edge, graph
    triggered_rules: List[str]