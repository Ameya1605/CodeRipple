from fastapi import APIRouter
from pydantic import BaseModel
from backend.jobs.tasks import run_index_task

router = APIRouter(prefix="/api/v1/repos", tags=["repos"])

class RepoRequest(BaseModel):
    repo_id: str
    path: str = ""
    url: str = ""

@router.post("")
async def register_repo(req: RepoRequest):
    return {"repo_id": req.repo_id, "status": "registered"}

@router.post("/{repo_id}/index")
async def trigger_index(repo_id: str, req: RepoRequest):
    path = req.path
    if req.url:
        path = f"/tmp/{repo_id}"
    task = run_index_task.delay(path, repo_id, req.url)
    return {"job_id": task.id}

@router.get("/{repo_id}/status")
async def get_status(repo_id: str, job_id: str):
    from backend.jobs.tasks import celery_app
    res = celery_app.AsyncResult(job_id)
    return {"job_id": job_id, "status": res.state, "pct": 100 if res.state == "SUCCESS" else 0}

@router.get("/{repo_id}/health")
async def get_repo_health(repo_id: str):
    from backend.intelligence.health import health_scorer
    return await health_scorer.calculate_repo_health(repo_id)
