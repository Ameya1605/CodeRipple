import yaml
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def load_repos(yaml_path: str = "repos.yaml") -> List[Dict[str, str]]:
    try:
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        return data.get("repos", [])
    except FileNotFoundError:
        logger.warning(f"repos.yaml not found at {yaml_path}")
        return []

def index_all_repos(yaml_path: str = "repos.yaml"):
    repos = load_repos(yaml_path)
    for repo in repos:
        repo_id = repo.get("id")
        path = repo.get("path")
        language = repo.get("language")
        logger.info(f"Cross-repo indexing stub: {repo_id} ({language}) at {path}")
        # In full implementation, this calls run_indexing(path, repo_id, full=True)
