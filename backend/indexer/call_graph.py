import os
import datetime
from typing import List
from backend.indexer.schema import CodeChunk

try:
    import git
except ImportError:
    git = None

def enrich_with_git_metrics(chunks: List[CodeChunk], repo_root: str) -> List[CodeChunk]:
    if not git:
        return chunks
        
    try:
        repo = git.Repo(repo_root)
    except Exception:
        # Invalid git repository or no git
        return chunks

    for chunk in chunks:
        try:
            # We look at the commits touching this specific file
            commits = list(repo.iter_commits(paths=chunk.file_path, max_count=50))
            if not commits:
                continue
                
            chunk.commit_hash = commits[0].hexsha
            chunk.commit_message = commits[0].message
            chunk.author = commits[0].author.name
            chunk.last_modified = datetime.datetime.fromtimestamp(commits[0].committed_date, tz=datetime.timezone.utc).isoformat()
            
            # Simple churn score based on commit frequency to this file
            chunk.churn_score = min(len(commits) / 20.0, 1.0)
            
            # Team owner extraction based on most frequent author for this file
            authors = [c.author.name for c in commits]
            if authors:
                chunk.team_owner = max(set(authors), key=authors.count)
                
        except Exception:
            pass
            
    return chunks

def build_call_edges(chunks: List[CodeChunk]) -> List[CodeChunk]:
    """
    Infers calls and called_by edges between chunks.
    Uses AST-extracted identifiers for higher accuracy.
    """
    qnames = {c.qualified_name: c for c in chunks}
    
    for chunk in chunks:
        # Save local names to resolve them
        local_calls = list(chunk.calls)
        chunk.calls = [] # Reset to store qualified names
        
        for qname, target_chunk in qnames.items():
            if qname == chunk.qualified_name:
                continue
            
            # Match against AST-extracted call identifiers
            if target_chunk.symbol_name in local_calls:
                if qname not in chunk.calls:
                    chunk.calls.append(qname)
                if chunk.qualified_name not in target_chunk.called_by:
                    target_chunk.called_by.append(chunk.qualified_name)
                    
    # Update fan_out metric
    for chunk in chunks:
        chunk.fan_out = len(chunk.calls)
        
    return chunks
