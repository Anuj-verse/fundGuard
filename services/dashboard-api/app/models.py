from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone
import uuid

class Base(DeclarativeBase):
    pass

class RiskScoreRecord(Base):
    __tablename__ = "risk_scores"

    transaction_id = Column(String, primary_key=True)
    sender_account_id = Column(String, index=True)
    receiver_account_id = Column(String)
    amount = Column(Float)
    unified_score = Column(Float)
    edge_score = Column(Float)
    graph_score = Column(Float)
    rule_score = Column(Float)
    graph_flags = Column(JSON)
    decision = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "sender_account_id": self.sender_account_id,
            "receiver_account_id": self.receiver_account_id,
            "amount": self.amount,
            "unified_score": self.unified_score,
            "decision": self.decision,
            "created_at": self.created_at.isoformat(),
        }

class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=lambda: f"CASE-{uuid.uuid4().hex[:8].upper()}")
    transaction_id = Column(String, index=True)
    sender_account_id = Column(String)
    unified_score = Column(Float)
    decision = Column(String)
    status = Column(String, default="OPEN") # OPEN, INVESTIGATING, PENDING_STR, CLOSED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "sender_account_id": self.sender_account_id,
            "unified_score": self.unified_score,
            "decision": self.decision,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
