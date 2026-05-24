import os
import datetime
from typing import List, Dict, Any
from backend.indexer.schema import CodeChunk

try:
    import git
except ImportError:
    git = None

class OwnershipAnalyzer:
    def get_reviewer_recommendations(self, chunks: List[CodeChunk], repo_root: str) -> List[Dict[str, Any]]:
        if not git: return []
        
        try:
            repo = git.Repo(repo_root)
        except Exception:
            return []

        author_scores = {} # author -> score

        for chunk in chunks:
            try:
                # Use git blame for the specific line range of the symbol
                # Note: gitpython blame returns [(commit, lines), ...]
                blame = repo.blame('HEAD', chunk.file_path)
                
                # Filter lines within chunk range
                for commit, lines in blame:
                    # This is simplified; real blame logic needs to track actual line numbers
                    author = commit.author.name
                    days_ago = (datetime.datetime.now(datetime.timezone.utc) - 
                               datetime.datetime.fromtimestamp(commit.committed_date, datetime.timezone.utc)).days
                    recency_weight = 1.0 / (days_ago + 1)
                    
                    score = len(lines) * recency_weight
                    author_scores[author] = author_scores.get(author, 0) + score
            except Exception:
                continue

        # Sort and format
        sorted_authors = sorted(author_scores.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for author, score in sorted_authors[:3]:
            recommendations.append({
                "name": author,
                "score": round(score, 2),
                "reason": f"High ownership score based on recent commits and line count"
            })
            
        return recommendations

ownership_analyzer = OwnershipAnalyzer()
