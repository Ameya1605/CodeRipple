import json
import os
import time
import asyncio
from backend.query.analyzer import analyze_impact
from backend.indexer.call_graph import build_call_edges as load_graph

def percentile(data, percent):
    if not data: return 0
    data.sort()
    k = (len(data) - 1) * (percent / 100.0)
    f = int(k)
    c = min(f + 1, len(data) - 1)
    if f == c:
        return data[f]
    return data[f] + (k - f) * (data[c] - data[f])

async def run_eval():
    with open("eval/golden_dataset.json", "r") as f:
        dataset = json.load(f)
        
    results = []
    latencies = []
    total_hallucinations = 0
    total_symbols = 0
    
    for case in dataset:
        start = time.time()
        try:
            # Create a mock chunk for the evaluation case
            changed_symbol = CodeChunk(
                chunk_id="eval-case",
                repo_id="eval-repo",
                file_path=case.get("file_path", "unknown.py"),
                symbol_type="function",
                symbol_name=case["changed_qualified_name"].split(".")[-1],
                qualified_name=case["changed_qualified_name"],
                start_line=1,
                end_line=10,
                signature="def eval_func()",
                content=case.get("content", ""), # Should be in golden dataset
                language="python"
            )
            
            res = await analyze_impact(changed_symbol, case["change_description"])
        except Exception as e:
            print(f"Failed {case['changed_qualified_name']}: {e}")
            continue
            
        latency = time.time() - start
        latencies.append(latency)
        
        # Recall@10
        top_10 = [d["qualified_name"] for d in res["retrieved_dependents"][:10]]
        true_deps = case["true_dependents"]
        recall = len(set(true_deps) & set(top_10)) / max(len(true_deps), 1)
        
        # FP Rate
        false_positives = len([d for d in top_10 if d not in true_deps]) / max(len(top_10), 1)
        
        # Risk Tier
        risk_match = 1 if res["validation"]["risk_tier"] == case["actual_risk_tier"] else 0
        
        # Hallucinations
        halls = len(res["validation"]["hallucinations"])
        total_hallucinations += halls
        total_symbols += max(10, halls)
        
        results.append({
            "case": case["changed_qualified_name"],
            "recall": recall,
            "fp_rate": false_positives,
            "risk_match": risk_match
        })
        
    avg_recall = sum(r["recall"] for r in results) / len(results) if results else 0
    avg_risk = sum(r["risk_match"] for r in results) / len(results) if results else 0
    avg_fp = sum(r["fp_rate"] for r in results) / len(results) if results else 0
    hall_rate = total_hallucinations / max(total_symbols, 1)
    
    print("=== Eval Results ===")
    print(f"Recall@10: {avg_recall:.2f}")
    print(f"Risk Accuracy: {avg_risk:.2f}")
    print(f"FP Rate: {avg_fp:.2f}")
    print(f"Hallucination Rate: {hall_rate:.2f}")
    
if __name__ == "__main__":
    asyncio.run(run_eval())
