from fastapi.testclient import TestClient
from src.main import app


def test_health_returns_contract_shape() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["message"] == "success"
    assert body["data"]["status"] == "ok"
    assert body["data"]["version"] == "0.1.0"
