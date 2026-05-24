import requests
import json

url = "http://localhost:8080/api/v1/analyze/symbol"
headers = {"Authorization": "Bearer dev-local-token", "Content-Type": "application/json"}
data = {
    "chunk": {
        "chunk_id": "mock1", 
        "repo_id": "core-api", 
        "file_path": "utils.py", 
        "symbol_type": "func", 
        "symbol_name": "calculate_impact", 
        "qualified_name": "calculate_impact", 
        "start_line": 1, 
        "end_line": 10, 
        "signature": "def mock()", 
        "content": "pass", 
        "language": "python"
    }, 
    "change_summary": "Modified logic"
}

res = requests.post(url, headers=headers, json=data)
print(res.status_code)
print(res.text)

