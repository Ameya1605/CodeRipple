import argparse
import os
import sys
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.indexer.pipeline import run_indexing

async def main_async():
    parser = argparse.ArgumentParser(description="Index repository")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--repo-id", default="local-repo")
    args = parser.parse_args()
    
    # The modern pipeline handles both Vector (Qdrant) and Graph (Neo4j)
    await run_indexing(args.repo, args.repo_id)
    print(f"Indexing complete for {args.repo_id}")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
