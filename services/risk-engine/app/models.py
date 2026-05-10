from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone
from uuid import uuid4

class Base(DeclarativeBase):
    pass

class RiskScoreRecord(Base):
    __tablename__ = "risk_scores"

    txn_id = Column(String, primary_key=True)
    sender_account = Column(String, index=True)
    receiver_account = Column(String)
    amount = Column(Float)
    final_score = Column(Float)
    edge_score = Column(Float)
    graph_score = Column(Float)
    alert_level = Column(String, index=True)
    patterns = Column(JSON)
    graph_features = Column(JSON)
    decision = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "txn_id": self.txn_id,
            "sender_account": self.sender_account,
            "receiver_account": self.receiver_account,
            "amount": self.amount,
            "final_score": self.final_score,
            "edge_score": self.edge_score,
            "graph_score": self.graph_score,
            "alert_level": self.alert_level,
            "patterns": self.patterns or [],
            "decision": self.decision,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=lambda: f"CASE-{uuid4().hex[:8].upper()}")
    txn_id = Column(String, index=True)
    sender_account = Column(String)
    final_score = Column(Float)
    alert_level = Column(String)
    patterns = Column(JSON)
    status = Column(String, default="OPEN")
    assigned_to = Column(String, nullable=True)
    llm_summary = Column(String, nullable=True)
    str_generated = Column(String, default="false")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "txn_id": self.txn_id,
            "sender_account": self.sender_account,
            "final_score": self.final_score,
            "alert_level": self.alert_level,
            "patterns": self.patterns or [],
            "status": self.status,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
