from fastapi.testclient import TestClient
from backend.main import app
from backend.auth.jwt_handler import create_access_token

client = TestClient(app)

def test_analyze_unauthorized():
    res = client.post("/api/v1/analyze/symbol", json={
        "chunk": {
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
        },
        "change_summary": "Added print"
    })
    
    assert res.status_code == 403 or res.status_code == 401

def test_analyze_authorized():
    token = create_access_token({
        "sub": "user-1",
        "username": "alice",
        "tenant_id": "tenant-A",
        "roles": ["developer"]
    })
    
    res = client.post("/api/v1/analyze/symbol", headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "chunk": {
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
            "language": "python",
            "risk_score_current": 0.0,
            "break_count_90d": 0,
            "churn_score": 0.0,
            "test_coverage_pct": 0.0,
            "is_on_critical_path": False
        },
        "change_summary": "Added print"
    })
    
    assert res.status_code == 200
    assert "request_id" in res.json()
