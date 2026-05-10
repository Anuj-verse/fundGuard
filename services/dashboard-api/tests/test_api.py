from fastapi.testclient import TestClient

from app.main import app, cases_store, ingest_risk_event, risk_history, txn_to_case

client = TestClient(app)


def reset_state():
    risk_history.clear()
    cases_store.clear()
    txn_to_case.clear()


def test_history_endpoints_return_recent_alerts_and_stats():
    reset_state()
    ingest_risk_event({"transaction_id": "txn-1", "decision": "APPROVE", "unified_score": 0.2, "received_at": "2026-05-10T10:00:00"})
    ingest_risk_event({"transaction_id": "txn-2", "decision": "REVIEW", "unified_score": 0.65, "received_at": "2026-05-10T10:01:00"})
    ingest_risk_event({"transaction_id": "txn-3", "decision": "REJECT", "unified_score": 0.92, "received_at": "2026-05-10T10:02:00"})

    alerts = client.get("/api/history/recent-alerts?limit=5")
    assert alerts.status_code == 200
    alert_payload = alerts.json()
    assert len(alert_payload) == 2
    assert alert_payload[0]["transaction_id"] == "txn-3"
    assert alert_payload[1]["transaction_id"] == "txn-2"

    stats = client.get("/api/history/dashboard-stats")
    assert stats.status_code == 200
    stats_payload = stats.json()
    assert stats_payload["liveEvents"] == 3
    assert stats_payload["activeAlerts"] == 2
    assert stats_payload["rejectedEvents"] == 1
    assert stats_payload["highRisk"] == 1


def test_cases_endpoint_supports_status_updates():
    reset_state()
    ingest_risk_event({"transaction_id": "txn-case", "decision": "REJECT", "unified_score": 0.99, "received_at": "2026-05-10T11:00:00"})

    cases = client.get("/api/cases")
    assert cases.status_code == 200
    payload = cases.json()
    assert len(payload) == 1
    assert payload[0]["status"] == "Open"

    updated = client.patch(f"/api/cases/{payload[0]['id']}", json={"status": "Closed"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "Closed"
