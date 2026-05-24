from fastapi import Depends, HTTPException, status, Request, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.auth.jwt_handler import decode_access_token
from backend.auth.models import User
from backend.config import AUTH_ENABLED, AUTH_DEV_BYPASS_TOKEN, ENVIRONMENT

security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> User:
    if not AUTH_ENABLED:
        if ENVIRONMENT != "production":
            return User(id="local_dev", username="developer", tenant_id="default", roles=["developer"])
        else:
            raise HTTPException(status_code=500, detail="AUTH_ENABLED=False is not allowed in production")

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    if AUTH_DEV_BYPASS_TOKEN and token == AUTH_DEV_BYPASS_TOKEN:
        return User(id="local_dev", username="developer", tenant_id="default", roles=["developer"])

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return User(
        id=payload.get("sub", "local_dev"),
        username=payload.get("username", "developer"),
        tenant_id=payload.get("tenant_id", "default"),
        roles=payload.get("roles", ["developer"])
    )

async def get_ws_user(websocket: WebSocket) -> User | None:
    if not AUTH_ENABLED:
        return User(id="local_dev", username="developer", tenant_id="default", roles=["developer"])

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing auth token")
        return None

    if AUTH_DEV_BYPASS_TOKEN and token == AUTH_DEV_BYPASS_TOKEN:
        return User(id="local_dev", username="developer", tenant_id="default", roles=["developer"])

    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return None

    return User(
        id=payload.get("sub", "local_dev"),
        username=payload.get("username", "developer"),
        tenant_id=payload.get("tenant_id", "default"),
        roles=payload.get("roles", ["developer"])
    )

def require_role(required_role: str):
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if required_role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return user
    return role_checker
