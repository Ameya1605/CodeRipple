from fastapi.testclient import TestClient
from backend.main import app
from backend.auth.jwt_handler import create_access_token

client = TestClient(app)

def test_health():
    res = client.get("/api/v1/health/codebase")
    assert res.status_code == 200
    assert "trend" in res.json()

def test_repos_register():
    res = client.post("/api/v1/repos", json={"repo_id": "r1", "path": "/foo"})
    assert res.status_code == 200
    assert res.json()["repo_id"] == "r1"

def test_analyze_symbol():
    chunk_data = {
        "chunk_id": "1",
        "repo_id": "r1",
        "file_path": "f.py",
        "symbol_type": "func",
        "symbol_name": "f",
        "qualified_name": "f",
        "start_line": 1,
        "end_line": 2,
        "signature": "def f()",
        "content": "pass",
        "language": "python"
    }
    token = create_access_token({
        "sub": "user-1",
        "username": "alice",
        "tenant_id": "tenant-A",
        "roles": ["developer"]
    })
    res = client.post("/api/v1/analyze/symbol", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "chunk": chunk_data,
        "change_summary": "Added print"
    })
    assert res.status_code == 200
    assert "request_id" in res.json()

def test_symbols_search():
    res = client.get("/api/v1/symbols/search?q=test")
    assert res.status_code == 200

def test_graph_blast_radius():
    res = client.get("/api/v1/graph/blast-radius?qname=test")
    assert res.status_code == 200

def test_feedback_incident():
    res = client.post("/api/v1/feedback/incident", json={"id": "123", "suspect_chunk_ids": ["c1"]})
    assert res.status_code == 200

def test_webhooks():
    res = client.post("/api/v1/webhooks/github")
    assert res.status_code == 204
    res = client.post("/api/v1/webhooks/pagerduty")
    assert res.status_code == 204
