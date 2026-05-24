import sys
import traceback

def run_diagnostic():
    print("=== Dependency Impact Analyzer Diagnostic ===")
    errors = 0

    print("\n1. Testing Backend Imports & Syntax...")
    try:
        from backend.config import validate_config
        from backend.main import app
        from backend.jobs.celery_app import celery_app
        from backend.jobs.tasks import run_analysis
        from backend.retrieval.retriever import retrieve_dependents
        from backend.indexer.vector_store import vector_store
        from backend.api.analyze import router
        print("[OK] Backend imports successful. No syntax errors.")
    except Exception as e:
        print("[FAIL] Backend import failed:")
        traceback.print_exc()
        errors += 1

    print("\n2. Testing Configuration Validation (F-8)...")
    try:
        from backend.config import validate_config
        validate_config()
        print("[OK] Config validation executed successfully.")
    except Exception as e:
        print("[FAIL] Config validation crashed:")
        traceback.print_exc()
        errors += 1

    print("\n3. Testing Pydantic Schema Validation (Fix #6)...")
    try:
        from backend.indexer.schema import CodeChunk
        chunk = CodeChunk(
            chunk_id="test",
            repo_id="test",
            file_path="test.py",
            symbol_type="func",
            symbol_name="test",
            qualified_name="test",
            start_line=1,
            end_line=2,
            signature="def test()",
            content="pass",
            language="python",
            embedding_vector=[0.1, 0.2, 0.3]
        )
        if getattr(chunk, "embedding_vector", None) == [0.1, 0.2, 0.3]:
            print("[OK] CodeChunk schema accepted explicit embedding_vector field.")
        else:
            print("[FAIL] CodeChunk schema failed to store embedding_vector.")
            errors += 1
    except Exception as e:
        print("[FAIL] Schema validation failed:")
        traceback.print_exc()
        errors += 1

    print("\n4. Testing Dependency Check (Neo4j APOC Fallback)...")
    try:
        from backend.graph.queries import BLAST_RADIUS_APOC, BLAST_RADIUS_NATIVE
        if "apoc.path.subgraphNodes" in BLAST_RADIUS_APOC and "MATCH path" in BLAST_RADIUS_NATIVE:
            print("[OK] Native cypher fallback logic for Neo4j is present.")
        else:
            print("[FAIL] Native cypher fallback logic is missing.")
            errors += 1
    except Exception as e:
        print("[FAIL] Query check failed:")
        traceback.print_exc()
        errors += 1
        
    print(f"\n=== Diagnostic Complete: {errors} Errors Found ===")
    sys.exit(errors)

if __name__ == "__main__":
    run_diagnostic()
