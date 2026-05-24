import os
from typing import List
from backend.indexer.schema import CodeChunk
try:
    from backend.indexer.parsers.parser_py import parse_python_file
    from backend.indexer.parsers.parser_ts import parse_ts_file
    from backend.indexer.parsers.parser_go import parse_go_file
    from backend.indexer.parsers.parser_rust import parse_rust_file
    from backend.indexer.parsers.parser_java import parse_java_file
except ImportError:
    # Handle gracefully when native tree-sitter extensions fail to compile on host
    parse_python_file = lambda p, r: []
    parse_ts_file = lambda p, r: []
    parse_go_file = lambda p, r: []
    parse_rust_file = lambda p, r: []
    parse_java_file = lambda p, r: []

def parse_file(file_path: str, repo_id: str) -> List[CodeChunk]:
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".py":
        return parse_python_file(file_path, repo_id)
    elif ext in [".ts", ".tsx", ".js", ".jsx"]:
        return parse_ts_file(file_path, repo_id)
    elif ext == ".go":
        return parse_go_file(file_path, repo_id)
    elif ext == ".rs":
        return parse_rust_file(file_path, repo_id)
    elif ext == ".java":
        return parse_java_file(file_path, repo_id)
    
    return []
