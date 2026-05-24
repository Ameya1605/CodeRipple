import argparse
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import networkx as nx
import re
import subprocess
from typing import List
from src.query.analyzer import analyze_change
from src.indexer.vector_store import qdrant, COLLECTION_NAME
from qdrant_client.models import Filter, FieldCondition, MatchText

def load_graph(repo_root: str) -> nx.DiGraph:
    graph_path = os.path.join(repo_root, ".dep_impact", "graph.gpickle")
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graph not found at {graph_path}. Run index.py first.")
    return nx.read_gpickle(graph_path)

def get_changed_symbols(file_path: str, repo_root: str) -> List[str]:
    # Run git diff
    cmd = ["git", "-C", repo_root, "diff", "HEAD", "--", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    symbols = []
    pattern = re.compile(r'^[-+]\s*(def|class|async def)\s+(\w+)')
    for line in result.stdout.splitlines():
        match = pattern.match(line)
        if match:
            symbols.append(match.group(2))
    return list(set(symbols))

def find_qualified_name(symbol_name: str, file_path: str = None) -> str:
    # Use exact match or naive text search. In qdrant, text match needs Text index.
    # For simplicity, we scroll and filter in Python if Qdrant text match isn't setup.
    # Let's scroll all and filter for now (not efficient, but works for Phase 7 MVP without text index)
    response = qdrant.scroll(collection_name=COLLECTION_NAME, limit=1000)
    matches = []
    if response and response[0]:
        for point in response[0]:
            chunk_name = point.payload.get("symbol_name", "")
            if chunk_name == symbol_name:
                if file_path and not point.payload.get("file_path", "").endswith(file_path):
                    continue
                matches.append(point.payload.get("qualified_name"))
                
    matches = list(set(matches))
    if not matches:
        raise ValueError(f"Symbol {symbol_name} not found in index.")
    if len(matches) > 1:
        raise ValueError(f"Multiple matches found for {symbol_name}: {matches}. Use --file to disambiguate.")
    return matches[0]

def main():
    parser = argparse.ArgumentParser(description="Dependency Impact Analyzer")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Symbol command
    sym_parser = subparsers.add_parser("symbol")
    sym_parser.add_argument("--name", required=True)
    sym_parser.add_argument("--file", required=False)
    sym_parser.add_argument("--change", required=True)
    sym_parser.add_argument("--repo", default=".")
    sym_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    # Diff command
    diff_parser = subparsers.add_parser("diff")
    diff_parser.add_argument("--file", required=True)
    diff_parser.add_argument("--repo", default=".")
    diff_parser.add_argument("--format", choices=["text", "json"], default="text")
    
    args = parser.parse_args()
    graph = load_graph(args.repo)
    
    if args.command == "symbol":
        qname = find_qualified_name(args.name, args.file)
        result = analyze_change(qname, args.change, args.repo, graph)
        
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            if result["validation"]["hallucinations"]:
                print(f"⚠️ WARNING: Possible hallucinations detected: {result['validation']['hallucinations']}\n")
            print(result["raw_response"])
            
    elif args.command == "diff":
        symbols = get_changed_symbols(args.file, args.repo)
        results = []
        for sym in symbols:
            try:
                qname = find_qualified_name(sym, args.file)
                # Auto-generate a generic change summary for diff mode if needed, or prompt
                res = analyze_change(qname, f"Modified {sym} in {args.file}", args.repo, graph)
                results.append((sym, res))
            except ValueError as e:
                print(f"Skipping {sym}: {e}")
                
        # Sort by risk
        risk_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
        results.sort(key=lambda x: risk_order.get(x[1]["validation"]["risk_tier"], 4))
        
        if args.format == "json":
            print(json.dumps([r[1] for r in results], indent=2))
        else:
            print("=== Diff Analysis Report ===")
            for sym, res in results:
                print(f"\n--- Symbol: {sym} (Risk: {res['validation']['risk_tier']}) ---")
                print(res["raw_response"])

if __name__ == "__main__":
    main()
