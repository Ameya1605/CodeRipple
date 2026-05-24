import json
import logging
from typing import List
from backend.indexer.schema import CodeChunk
from backend.config import LLM_MODEL

logger = logging.getLogger(__name__)

try:
    import os
    from anthropic import AsyncAnthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        client = AsyncAnthropic(api_key=api_key)
    else:
        client = None
except ImportError:
    client = None

DEAD_CODE_PROMPT = """
You are a static analysis system. For each function below, classify it as:
  dead        — unreachable; safe to delete
  dynamic     — called via getattr, registry, or plugin pattern
  entry_point — invoked from outside (CLI, cron, webhook, framework hook)
  unknown     — insufficient context

Output ONLY a JSON array, one object per function:
[{"qualified_name": "...", "verdict": "dead|dynamic|entry_point|unknown",
  "reason": "one sentence", "confidence": 0.0-1.0}]

Functions to classify:
{candidates_json}
"""

async def classify_dead_code_batch(chunks: List[CodeChunk]) -> List[CodeChunk]:
    if not client:
        logger.warning("Anthropic client not initialized. Cannot classify dead code.")
        return chunks
        
    candidates = []
    for chunk in chunks:
        candidates.append({
            "qualified_name": chunk.qualified_name,
            "code": chunk.content[:200] # Signature and start
        })
        
    prompt = DEAD_CODE_PROMPT.format(candidates_json=json.dumps(candidates, indent=2))
    
    try:
        response = await client.messages.create(
            model=LLM_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text
        start_idx = text.find('[')
        end_idx = text.rfind(']') + 1
        
        if start_idx != -1 and end_idx != 0:
            results = json.loads(text[start_idx:end_idx])
            verdicts = {r["qualified_name"]: r["verdict"] for r in results if "qualified_name" in r and "verdict" in r}
            
            for chunk in chunks:
                if chunk.qualified_name in verdicts:
                    chunk.dead_code_verdict = verdicts[chunk.qualified_name]
    except Exception as e:
        logger.error(f"Dead code classification failed: {e}")
        
    return chunks
