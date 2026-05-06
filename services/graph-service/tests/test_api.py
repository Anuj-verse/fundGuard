from fastapi.testclient import TestClient
import pytest
from app.main import app as fastapi_app

def test_health_check():
    # Mock Neo4j and Kafka before running
    with TestClient(fastapi_app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

def test_get_active_patterns():
    # Mocking patterns
    import app.main
    app.main.active_patterns = [
        {"transaction_id": "TXN-1", "pattern": {"type": "layering"}}
    ]
    with TestClient(fastapi_app) as client:
        response = client.get("/patterns/active")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["transaction_id"] == "TXN-1"

def test_get_ego_network(monkeypatch):
    class MockNeo4j:
        def get_ego_network(self, account_id, depth):
            return {"nodes": [{"id": account_id}], "edges": []}
        def close(self):
            pass

    import app.main
    with TestClient(fastapi_app) as client:
        app.main.neo4j_graph = MockNeo4j()
        response = client.get("/graph/ACC-123?depth=1")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert data["nodes"][0]["id"] == "ACC-123"
