import hmac
import hashlib
import json
import logging
from fastapi import APIRouter, Request, Response, Header
from backend.config import GITHUB_WEBHOOK_SECRET

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

@router.post("/github")
async def github_webhook(
    request: Request, 
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None)
):
    body = await request.body()
    
    # Verify signature
    if GITHUB_WEBHOOK_SECRET:
        signature = "sha256=" + hmac.new(
            GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, x_hub_signature_256 or ""):
            return Response(status_code=401)

    payload = json.loads(body)
    
    if x_github_event == "pull_request":
        action = payload.get("action")
        if action in ["opened", "synchronize"]:
            pr_data = payload["pull_request"]
            logger.info(f"PR {action}: {pr_data['html_url']}")
            
    return Response(status_code=204)

@router.post("/pagerduty")
async def pagerduty_webhook(request: Request):
    return Response(status_code=204)
