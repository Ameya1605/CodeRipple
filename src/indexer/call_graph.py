import os
import networkx as nx
import git
import datetime
from typing import List, Dict, Tuple
import tree_sitter
import tree_sitter_python
from collections import defaultdict
from src.indexer.schema import CodeChunk
from src.indexer.ast_parser import PARSER

def _get_call_nodes(node):
    calls = []
    def walk(n):
        if n.type == "call":
            calls.append(n)
        for child in n.children:
            walk(child)
    walk(node)
    return calls

def _get_call_name(call_node, source_bytes: bytes) -> str:
    func_node = call_node.child_by_field_name("function")
    if not func_node:
        return ""
    if func_node.type == "identifier":
        return source_bytes[func_node.start_byte:func_node.end_byte].decode("utf-8")
    elif func_node.type == "attribute":
        attr_node = func_node.child_by_field_name("attribute")
        if attr_node:
            return source_bytes[attr_node.start_byte:attr_node.end_byte].decode("utf-8")
    return source_bytes[func_node.start_byte:func_node.end_byte].decode("utf-8")

def _parse_imports(file_chunks: List[CodeChunk]) -> Dict[str, str]:
    # Maps local name to fully qualified imported name
    imports_map = {}
    for chunk in file_chunks:
        if chunk.symbol_type == "module":
            for imp in chunk.imports:
                # Naive parsing of import statements for Phase 3
                if imp.startswith("from"):
                    parts = imp.split(" import ")
                    if len(parts) == 2:
                        module = parts[0].replace("from ", "").strip()
                        names = parts[1].split(",")
                        for name in names:
                            name = name.strip()
                            if " as " in name:
                                orig, alias = name.split(" as ")
                                imports_map[alias.strip()] = f"{module}.{orig.strip()}"
                            else:
                                imports_map[name] = f"{module}.{name}"
                elif imp.startswith("import"):
                    parts = imp.replace("import ", "").split(",")
                    for part in parts:
                        part = part.strip()
                        if " as " in part:
                            orig, alias = part.split(" as ")
                            imports_map[alias.strip()] = orig.strip()
                        else:
                            imports_map[part] = part
    return imports_map

def build_call_graph(chunks: List[CodeChunk], repo_root: str) -> nx.DiGraph:
    graph = nx.DiGraph()
    
    # 1. Add all chunks as nodes
    chunks_by_qname = {chunk.qualified_name: chunk for chunk in chunks}
    chunks_by_file = defaultdict(list)
    for chunk in chunks:
        graph.add_node(chunk.qualified_name, type=chunk.symbol_type)
        chunks_by_file[chunk.file_path].append(chunk)

    # 2. Extract calls and populate edges
    for file_path, file_chunks in chunks_by_file.items():
        with open(file_path, "rb") as f:
            source_bytes = f.read()
        tree = PARSER.parse(source_bytes)
        root_node = tree.root_node
        
        # Build symbol map for this file
        local_symbols = {c.symbol_name: c.qualified_name for c in file_chunks if c.symbol_type in ("function", "method", "class")}
        imports_map = _parse_imports(file_chunks)
        
        # Re-walk AST to find functions and calls
        # To match nodes to chunks, we do it by name (simplified)
        def process_function_calls(node, chunk_qname):
            calls = _get_call_nodes(node)
            chunk_obj = chunks_by_qname[chunk_qname]
            
            for call_node in calls:
                called_name = _get_call_name(call_node, source_bytes)
                if not called_name:
                    continue
                
                # Resolve name
                resolved_qname = None
                if called_name in local_symbols:
                    resolved_qname = local_symbols[called_name]
                elif called_name in imports_map:
                    resolved_qname = imports_map[called_name]
                else:
                    # check if it matches a method by name globally (naive)
                    pass
                
                if resolved_qname and resolved_qname in chunks_by_qname:
                    chunk_obj.calls.append(resolved_qname)
                    graph.add_edge(chunk_qname, resolved_qname)
                else:
                    chunk_obj.calls.append(f"external::{called_name}")
        
        def walk_for_chunks(n, class_name=None):
            if n.type in ["function_definition", "async_function_definition"]:
                name_node = n.child_by_field_name("name")
                if name_node:
                    name = source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")
                    qname_to_look = local_symbols.get(name)
                    if class_name and not qname_to_look: # Might be method
                        # find method qname
                        for local_name, qn in local_symbols.items():
                            if qn.endswith(f".{class_name}.{name}"):
                                qname_to_look = qn
                                break
                    if qname_to_look:
                        process_function_calls(n, qname_to_look)
            elif n.type == "class_definition":
                name_node = n.child_by_field_name("name")
                if name_node:
                    class_name = source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")
                    for child in n.children:
                        walk_for_chunks(child, class_name)
            else:
                for child in n.children:
                    walk_for_chunks(child, class_name)

        walk_for_chunks(root_node)

    # 3. Populate called_by
    for chunk in chunks:
        if chunk.qualified_name in graph:
            chunk.called_by = list(graph.predecessors(chunk.qualified_name))

    return graph

def _get_git_stats(file_path: str, repo_root: str) -> Tuple[float, str]:
    try:
        repo = git.Repo(repo_root)
        rel_path = os.path.relpath(file_path, repo_root)
        
        # total commits
        total_commits = list(repo.iter_commits(paths=rel_path))
        if not total_commits:
            return 0.0, ""
            
        # commits in last 90 days
        ninety_days_ago = datetime.datetime.now() - datetime.timedelta(days=90)
        recent_commits = [c for c in total_commits if c.committed_datetime.replace(tzinfo=None) >= ninety_days_ago]
        
        churn_score = len(recent_commits) / len(total_commits)
        last_modified = total_commits[0].committed_datetime.isoformat()
        return churn_score, last_modified
    except Exception:
        return 0.0, ""

def populate_git_metrics(chunks: List[CodeChunk], repo_root: str):
    file_stats = {}
    
    # Precompute per-file to save time
    for chunk in chunks:
        if chunk.file_path not in file_stats:
            file_stats[chunk.file_path] = _get_git_stats(chunk.file_path, repo_root)
            
        churn_score, last_modified = file_stats[chunk.file_path]
        chunk.churn_score = churn_score
        chunk.last_modified = last_modified
        
        # Simplified team owner (fallback to empty or naive)
        chunk.team_owner = "unknown"

def get_blast_radius(graph: nx.DiGraph, qualified_name: str, max_depth: int = 3) -> Dict[str, List[str]]:
    result = {"direct": [], "depth_2": [], "depth_3": [], "all": []}
    if qualified_name not in graph:
        return result
        
    visited = set()
    queue = [(qualified_name, 0)]
    
    while queue:
        current, depth = queue.pop(0)
        
        if depth > 0 and current not in visited:
            visited.add(current)
            result["all"].append(current)
            if depth == 1:
                result["direct"].append(current)
            elif depth == 2:
                result["depth_2"].append(current)
            elif depth == 3:
                result["depth_3"].append(current)
                
        if depth < max_depth:
            for pred in graph.predecessors(current):
                if pred not in visited:
                    queue.append((pred, depth + 1))
                    
    return result
