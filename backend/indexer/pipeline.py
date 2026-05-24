import os
import re
import logging
from typing import List
from backend.indexer.parsers import parse_file
from backend.indexer.call_graph import enrich_with_git_metrics, build_call_edges
from backend.indexer.embedder import embed_chunks
from backend.indexer.vector_store import vector_store

logger = logging.getLogger(__name__)

ENTRY_POINT_PATTERNS = {
    "python":     [r"def main\(", r"@app\.route", r"@celery\.task",
                   r"@pytest\.fixture", r'if __name__ == "__main__"'],
    "typescript": [r"export default function", r"app\.(get|post|put|delete)\(",
                   r"export default.*Page"],
    "go":         [r"func main\(\)", r"^package main"],
    "rust":       [r"fn main\(\)", r"#\[tokio::main\]", r"#\[actix_web::main\]"],
    "java":       [r"public static void main\(String", r"@RestController",
                   r"@Test"],
}

def detect_entry_points(repo_root: str, language: str) -> List[str]:
    """
    Scans the repository for entry points based on language patterns.
    Returns a list of file paths that contain one or more entry points.
    """
    patterns = ENTRY_POINT_PATTERNS.get(language, [])
    if not patterns:
        return []

    compiled_patterns = [re.compile(p) for p in patterns]
    entry_points = []

    for root, _, files in os.walk(repo_root):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if language == "python" and ext != ".py": continue
            if language == "typescript" and ext not in [".ts", ".tsx"]: continue
            if language == "go" and ext != ".go": continue
            if language == "rust" and ext != ".rs": continue
            if language == "java" and ext != ".java": continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for pattern in compiled_patterns:
                        if pattern.search(content):
                            entry_points.append(file_path)
                            break  # File is an entry point, no need to check other patterns
            except Exception:
                pass

    return list(set(entry_points))

async def run_indexing(repo_root: str, repo_id: str, full: bool = True):
    logger.info(f"Starting indexing for repo: {repo_id}")
    
    # 1. Parse all files
    all_chunks = []
    for root, _, files in os.walk(repo_root):
        # Skip common ignored dirs
        if any(ignored in root for ignored in ['.git', 'node_modules', 'venv', '__pycache__']):
            continue
            
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, repo_root)
            try:
                chunks = parse_file(abs_path, repo_id)
                if chunks:
                    for chunk in chunks:
                        chunk.file_path = rel_path
                    all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error parsing {abs_path}: {e}")
                
    logger.info(f"Parsed {len(all_chunks)} chunks from {repo_root}")
    if not all_chunks:
        return []
        
    # 2. Enrich with git metrics
    logger.info("Enriching with git metrics...")
    all_chunks = enrich_with_git_metrics(all_chunks, repo_root)
    
    # 3. Build call edges
    logger.info("Building call graph edges...")
    all_chunks = build_call_edges(all_chunks)
    
    # 4. Entry points (Critical path identification)
    # Simple strategy: if a chunk is in an entry point file, mark as critical
    for lang in ENTRY_POINT_PATTERNS.keys():
        entry_files = detect_entry_points(repo_root, lang)
        for chunk in all_chunks:
            if chunk.file_path in entry_files and chunk.language == lang:
                chunk.is_on_critical_path = True
                
    # 5. Embed chunks
    logger.info("Generating embeddings...")
    all_chunks = await embed_chunks(all_chunks)
    
    # 6. Init collections and upsert to Qdrant
    logger.info("Upserting vectors to Qdrant...")
    await vector_store.init_collections()
    await vector_store.upsert_chunks(all_chunks)
    
    # 7. Build implicit edges
    logger.info("Building implicit semantic edges...")
    from backend.indexer.implicit_graph import build_implicit_edges
    await build_implicit_edges(all_chunks)
    
    logger.info(f"Completed indexing for repo: {repo_id}")
    return all_chunks
