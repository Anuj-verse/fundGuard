from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app, get_db

client = TestClient(app)


class FakeScalarsResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeExecuteResult:
    def __init__(self, *, scalar_value=None, scalars_rows=None, one=None):
        self._scalar_value = scalar_value
        self._scalars_rows = scalars_rows
        self._one = one

    def scalar(self):
        return self._scalar_value

    def scalars(self):
        return FakeScalarsResult(self._scalars_rows or [])

    def scalar_one_or_none(self):
        return self._one


class FakeSession:
    def __init__(self, results):
        self._results = list(results)
        self.committed = False

    async def execute(self, _):
        return self._results.pop(0)

    async def commit(self):
        self.committed = True

    async def refresh(self, _):
        return None


def _override_db(session):
    async def _get_db_override():
        yield session

    app.dependency_overrides[get_db] = _get_db_override


def _clear_db_override():
    app.dependency_overrides.pop(get_db, None)


def test_recent_alerts_endpoint_returns_flagged_records():
    rows = [
        SimpleNamespace(transaction_id="TXN-2", unified_score=0.91, decision="REJECT"),
        SimpleNamespace(transaction_id="TXN-1", unified_score=0.66, decision="REVIEW"),
    ]
    session = FakeSession([FakeExecuteResult(scalars_rows=rows)])
    _override_db(session)
    try:
        response = client.get("/api/recent-alerts?limit=5")
    finally:
        _clear_db_override()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["transaction_id"] == "TXN-2"
    assert payload[1]["decision"] == "REVIEW"


def test_dashboard_stats_endpoint_aggregates_counts():
    session = FakeSession(
        [
            FakeExecuteResult(scalar_value=4),  # total
            FakeExecuteResult(scalar_value=1),  # rejects
            FakeExecuteResult(scalar_value=2),  # alerts
        ]
    )
    _override_db(session)
    try:
        response = client.get("/api/stats")
    finally:
        _clear_db_override()

    assert response.status_code == 200
    payload = response.json()
    assert payload["liveEvents"] == 4
    assert payload["rejectedEvents"] == 1
    assert payload["activeAlerts"] == 2
    assert payload["fraudRate"] == "25.00%"


def test_cases_endpoints_list_and_update_status():
    class FakeCase:
        def __init__(self, case_id, status):
            self.id = case_id
            self.status = status

        def to_dict(self):
            return {"id": self.id, "status": self.status}

    list_case = FakeCase("CASE-1", "OPEN")
    session_list = FakeSession([FakeExecuteResult(scalars_rows=[list_case])])
    _override_db(session_list)
    try:
        list_response = client.get("/api/cases")
    finally:
        _clear_db_override()

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == "CASE-1"

    update_case = FakeCase("CASE-1", "OPEN")
    session_update = FakeSession([FakeExecuteResult(one=update_case)])
    _override_db(session_update)
    try:
        patch_response = client.patch("/api/cases/CASE-1", json={"status": "INVESTIGATING"})
    finally:
        _clear_db_override()

    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "INVESTIGATING"
    assert update_case.status == "INVESTIGATING"
    assert session_update.committed is True
