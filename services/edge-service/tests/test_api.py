from fastapi.testclient import TestClient
from app.main import app as fastapi_app

client = TestClient(fastapi_app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"

def test_score_endpoint_mocked_model():
    # Mock the scorer for tests to avoid needing the real ONNX model file
    class MockScorer:
        def score(self, features):
            return 0.95, "BLOCK"

    import app.main
    
    payload = {
        "transaction_id": "TEST-123",
        "timestamp": "2024-05-06T12:00:00Z",
        "sender_account_id": "ACC-1",
        "receiver_account_id": "ACC-2",
        "amount": 500000.0,
        "channel": "UPI",
        "sender_geo_latitude": 12.97,
        "sender_geo_longitude": 77.59,
        "receiver_geo_latitude": 28.70,
        "receiver_geo_longitude": 77.10
    }

    with TestClient(fastapi_app) as client:
        app.main.scorer = MockScorer()
        response = client.post("/score", json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["transaction_id"] == "TEST-123"
        assert data["decision"] == "BLOCK"
        assert "latency_ms" in data
        assert "features_used" in data
        assert data["features_used"]["amount"] == 500000.0
