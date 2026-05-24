import logging
from typing import Dict, Any, List
from backend.graph.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

class HealthScorer:
    async def calculate_repo_health(self, repo_id: str) -> Dict[str, Any]:
        """
        Calculates a 0-100 health score for a repository.
        """
        async with neo4j_client.session() as session:
            # 1. Total active symbols
            res = await session.run(
                "MATCH (s:Symbol {repo_id: $repo_id, active: true}) RETURN count(s) as count",
                repo_id=repo_id
            )
            total_symbols = (await res.single())["count"]
            if total_symbols == 0:
                return {"score": 100, "metrics": {}}

            # 2. Critical path coverage (Percentage of critical path symbols with tests)
            res = await session.run(
                """
                MATCH (s:Symbol {repo_id: $repo_id, active: true, is_on_critical_path: true})
                WITH count(s) as total_critical
                MATCH (s:Symbol {repo_id: $repo_id, active: true, is_on_critical_path: true})
                WHERE s.test_coverage > 0.5
                RETURN total_critical, count(s) as covered_critical
                """,
                repo_id=repo_id
            )
            record = await res.single()
            total_critical = record["total_critical"]
            covered_critical = record["covered_critical"]
            critical_coverage = (covered_critical / total_critical) if total_critical > 0 else 1.0

            # 3. Structural Complexity (Average Fan-Out)
            res = await session.run(
                "MATCH (s:Symbol {repo_id: $repo_id, active: true}) RETURN avg(s.fan_out) as avg_fan_out",
                repo_id=repo_id
            )
            avg_fan_out = (await res.single())["avg_fan_out"] or 0.0
            complexity_penalty = min(avg_fan_out / 10.0, 0.5) # Max 50% penalty for extreme fan-out

            # 4. Final Score calculation
            # Base 100 - (1 - critical_coverage)*50 - complexity_penalty*50
            score = 100 - ((1 - critical_coverage) * 50) - (complexity_penalty * 50)
            
            return {
                "score": round(max(0, score), 2),
                "metrics": {
                    "total_symbols": total_symbols,
                    "critical_path_count": total_critical,
                    "critical_coverage": round(critical_coverage * 100, 2),
                    "avg_fan_out": round(avg_fan_out, 2)
                }
            }

health_scorer = HealthScorer()
