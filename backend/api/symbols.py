from fastapi import APIRouter, Query
from typing import List, Optional

router = APIRouter(prefix="/api/v1/symbols", tags=["symbols"])

@router.get("/search")
async def search_symbols(q: str = Query(""), repo_id: Optional[str] = None):
    return []

@router.get("/{chunk_id}")
async def get_symbol(chunk_id: str):
    return {"chunk_id": chunk_id}
