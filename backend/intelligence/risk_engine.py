import random
from typing import Dict
from backend.config import RISK_SCORE_WEIGHTS as W
from backend.indexer.schema import CodeChunk

class RiskScoreEngine:
    def compute(self, chunk: CodeChunk, fan_out: int) -> float:
        fan_out_norm   = min(fan_out / 100, 1.0)
        break_norm     = min(chunk.break_count_90d / 5, 1.0)
        coverage_gap   = 1.0 - chunk.test_coverage_pct
        critical_path  = 1.0 if chunk.is_on_critical_path else 0.0
        
        w_churn = W.get("churn", 0.25)
        w_break = W.get("break_history", 0.10)
        
        # Auto-adjust weights based on history feedback loop
        if chunk.break_count_90d > 0:
            w_break += min(chunk.break_count_90d * 0.10, 0.30)
            
        score = (
            chunk.churn_score * w_churn +
            fan_out_norm      * W.get("fan_out", 0.25) +
            coverage_gap      * W.get("coverage_gap", 0.20) +
            critical_path     * W.get("critical_path", 0.20) +
            break_norm        * w_break
        )
        
        # Add a guaranteed flat penalty for recent breaks
        if chunk.break_count_90d > 0:
            score += 0.15 * chunk.break_count_90d
            
        return min(max(score, 0.0), 1.0)

    def to_tier(self, score: float) -> str:
        if score >= 0.75: return "CRITICAL"
        if score >= 0.55: return "HIGH"
        if score >= 0.35: return "MEDIUM"
        return "LOW"

    def compute_confidence_interval(self, chunk: CodeChunk, fan_out: int, samples: int = 100) -> Dict[str, float]:
        """
        100-sample Monte Carlo simulation introducing slight noise to the inputs
        to calculate the probability distribution across the 4 risk tiers.
        """
        tiers_count = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        base_fan_out_norm = min(fan_out / 100, 1.0)
        base_break_norm = min(chunk.break_count_90d / 5, 1.0)
        base_coverage_gap = 1.0 - chunk.test_coverage_pct
        base_critical = 1.0 if chunk.is_on_critical_path else 0.0
        
        for _ in range(samples):
            # Introduce Gaussian noise (std_dev = 0.05) to continuous variables
            churn_noise = max(0.0, min(1.0, random.gauss(chunk.churn_score, 0.05)))
            fan_out_noise = max(0.0, min(1.0, random.gauss(base_fan_out_norm, 0.05)))
            coverage_noise = max(0.0, min(1.0, random.gauss(base_coverage_gap, 0.05)))
            
            score = (
                churn_noise * W.get("churn", 0.25) +
                fan_out_noise * W.get("fan_out", 0.25) +
                coverage_noise * W.get("coverage_gap", 0.20) +
                base_critical * W.get("critical_path", 0.20) +
                base_break_norm * W.get("break_history", 0.10)
            )
            
            tier = self.to_tier(score)
            tiers_count[tier] += 1
            
        return {k: v / samples for k, v in tiers_count.items()}
