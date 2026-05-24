from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])

@router.get("/blast-radius")
async def get_blast_radius(qname: str):
    return {"nodes": [], "edges": []}
