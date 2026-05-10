from pathlib import Path
from fastapi.testclient import TestClient
import app.main as dashboard_main
import pytest

client = TestClient(dashboard_main.app)


@pytest.fixture(autouse=True)
def reset_db_path():
    original_db_path = dashboard_main.DB_PATH
    yield
    dashboard_main.DB_PATH = original_db_path


def _seed(db_path: Path):
    dashboard_main.DB_PATH = str(db_path)
    dashboard_main.init_db()
    dashboard_main.persist_risk_score({"transaction_id": "TXN-1", "unified_score": 0.20, "decision": "APPROVE"})
    dashboard_main.persist_risk_score({"transaction_id": "TXN-2", "unified_score": 0.62, "decision": "REVIEW"})
    dashboard_main.persist_risk_score({"transaction_id": "TXN-3", "unified_score": 0.91, "decision": "REJECT"})


def test_recent_alerts_and_stats(tmp_path):
    _seed(tmp_path / "dashboard.db")

    alerts_resp = client.get("/api/recent-alerts")
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) == 2
    assert all(alert["decision"] != "APPROVE" for alert in alerts)
    assert alerts[0]["decision"] in {"REJECT", "REVIEW"}

    stats_resp = client.get("/api/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["liveEvents"] == 3
    assert stats["activeAlerts"] == 2
    assert stats["highRisk"] == 1


def test_cases_list(tmp_path):
    _seed(tmp_path / "cases.db")

    resp = client.get("/api/cases")
    assert resp.status_code == 200
    cases = resp.json()
    assert len(cases) == 2
    assert cases[0]["id"].startswith("CASE-")
