from fastapi.testclient import TestClient
from main import app

def test_health_check_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        # It should return a valid status code. If MongoDB isn't running locally, it will be 503.
        # If it is running, it will be 200.
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "database" in data
