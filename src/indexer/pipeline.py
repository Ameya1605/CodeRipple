import os
from src.indexer.ast_parser import parse_file
from src.indexer.call_graph import build_call_graph, populate_git_metrics
from src.indexer.embedder import embed_chunks
from src.indexer.vector_store import init_collection, upsert_chunks

def run_indexing(repo_root: str):
    print("Starting indexing pipeline...")
    all_chunks = []
    
    for root, dirs, files in os.walk(repo_root):
        if "__pycache__" in root or ".git" in root or "venv" in root:
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".py"):
                print(f"Parsing {file_path}...")
                
                # Check generated
                is_gen = False
                with open(file_path, "r", encoding="utf-8") as f:
                    for _ in range(5):
                        line = f.readline()
                        if "DO NOT EDIT" in line or "Code generated" in line or "@generated" in line:
                            is_gen = True
                            break
                            
                chunks = parse_file(file_path, repo_root)
                if is_gen:
                    for c in chunks:
                        c.is_generated = True
                        c.symbol_type = "module" # fallback for generated
                all_chunks.extend(chunks)
                
    print(f"Parsed {len(all_chunks)} chunks. Building call graph...")
    graph = build_call_graph(all_chunks, repo_root)
    populate_git_metrics(all_chunks, repo_root)
    
    print("Embedding chunks...")
    chunks_with_vectors = embed_chunks(all_chunks)
    
    from src.indexer.vector_store import qdrant, COLLECTION_NAME
    from src.config import EMBEDDING_MODEL
    
    try:
        res = qdrant.scroll(collection_name=COLLECTION_NAME, limit=1)
        if res and res[0]:
            exist_model = res[0][0].payload.get("embedding_model_version")
            if exist_model and exist_model != EMBEDDING_MODEL:
                print(f"ERROR: Embedding model mismatch. Index={exist_model}, Current={EMBEDDING_MODEL}")
                return None
    except Exception:
        pass

    print("Initializing Qdrant and upserting...")
    init_collection()
    upsert_chunks(chunks_with_vectors)
    
    print("Indexing complete.")
    return graph
