from pydantic import BaseModel
from typing import List

class User(BaseModel):
    id: str
    username: str
    tenant_id: str
    roles: List[str]

class Tenant(BaseModel):
    id: str
    name: str
    allowed_repos: List[str]
