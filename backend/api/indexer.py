import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.indexer.delta_indexer import delta_indexer

router = APIRouter(prefix="/index", tags=["indexing"])
logger = logging.getLogger(__name__)

class DeltaIndexRequest(BaseModel):
    repo_id: str
    repo_root: str
    file_path: str
    content: str

@router.post("/delta")
async def index_delta(request: DeltaIndexRequest):
    try:
        result = await delta_indexer.index_file_delta(
            repo_id=request.repo_id,
            repo_root=request.repo_root,
            file_path=request.file_path,
            content=request.content
        )
        return result
    except Exception as e:
        logger.error(f"Delta indexing API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
