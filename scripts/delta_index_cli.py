import argparse
import os
import requests
import json

def main():
    parser = argparse.ArgumentParser(description="Delta index a specific file.")
    parser.add_argument("--file", required=True, help="Path to the file to index")
    parser.add_argument("--repo-id", default="default", help="Repository ID")
    parser.add_argument("--api-url", default="http://localhost:8080", help="API URL")
    
    args = parser.parse_args()
    
    repo_root = os.getcwd()
    abs_path = os.path.abspath(args.file)
    rel_path = os.path.relpath(abs_path, repo_root)
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        response = requests.post(
            f"{args.api_url}/index/delta",
            json={
                "repo_id": args.repo_id,
                "repo_root": repo_root,
                "file_path": rel_path,
                "content": content
            }
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ Indexed {rel_path}: {result.get('count')} symbols found.")
        
    except Exception as e:
        print(f"❌ Failed to index {rel_path}: {e}")

if __name__ == "__main__":
    main()
