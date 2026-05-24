import re
from typing import List, Dict, Any
from src.retrieval.retriever import RetrievedDependent

def validate_response(response_text: str, retrieved: List[RetrievedDependent]) -> Dict[str, Any]:
    risk_tier = "UNKNOWN"
    hallucinations = []
    
    # Parse Risk Tier
    match = re.search(r"## Risk Tier\s*(CRITICAL|HIGH|MEDIUM|LOW)", response_text)
    if match:
        risk_tier = match.group(1)
        
    # Check sections
    has_impact = "## Impact Summary" in response_text
    is_valid = has_impact and risk_tier != "UNKNOWN"
    
    # Extract dependents and check for hallucinations
    dep_match = re.search(r"## Direct Dependents\n(.*?)(?=\n## |\Z)", response_text, re.DOTALL)
    if dep_match:
        deps_text = dep_match.group(1)
        # Find symbol-like patterns
        symbols = re.findall(r"`?([a-zA-Z0-9_\.]+)`?", deps_text)
        
        valid_qnames = {dep.chunk.qualified_name for dep in retrieved}
        valid_names = {dep.chunk.symbol_name for dep in retrieved}
        
        for sym in symbols:
            if len(sym) < 4: continue # skip small words
            # Naive hallucination check
            if sym not in valid_qnames and sym not in valid_names and "." in sym:
                # possible hallucination
                hallucinations.append(sym)
                
    return {
        "is_valid": is_valid,
        "risk_tier": risk_tier,
        "hallucinations": list(set(hallucinations)),
        "raw_response": response_text
    }
