import os

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert isinstance(body["uptime_seconds"], int)
    if not os.environ.get("WEBUI_CI_TEST"):
        assert body["frontend_built"] is True
