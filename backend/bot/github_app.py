import hmac
import hashlib
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def verify_github_signature(payload_body: bytes, signature_header: str, secret_token: str) -> bool:
    if not signature_header:
        return False
    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)

async def handle_pull_request_event(payload: Dict[str, Any]):
    action = payload.get("action")
    if action not in ["opened", "synchronize", "reopened"]:
        return
        
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    
    pr_number = pr_data.get("number")
    repo_name = repo_data.get("full_name")
    
    logger.info(f"Triggering analysis for PR #{pr_number} on {repo_name}")
    # Integration logic for semantic diff extraction and celery dispatch
