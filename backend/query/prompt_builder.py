"""
Prompt builder — Fix #5: Returns separate system and user messages.
"""
from typing import List, Dict, Any
from backend.indexer.schema import CodeChunk
from backend.query.system_prompt import SYSTEM_PROMPT


def build_query_prompt(changed_symbol: CodeChunk, change_summary: str, retrieved: List[CodeChunk], graph_summary: Dict[str, Any], cdl_delta: Any = None) -> List[Dict[str, str]]:
    """
    Assembles the 4 XML context blocks: CHANGED_SYMBOL, DETERMINISTIC_CONTRACT_DIFF, CALL_GRAPH_SUMMARY, and RETRIEVED_DEPENDENTS.
    Now also includes LEARNED_FEEDBACK for few-shot learning.
    
    Fix #5: Returns separate system/user messages so the LLM client can properly
    set system_instruction on the Gemini API.
    """
    from backend.intelligence.feedback_loop import FeedbackLoopEngine
    engine = FeedbackLoopEngine()
    corrected_examples = engine.get_corrected_examples(limit=3)
    
    feedback_xml = ""
    if corrected_examples:
        feedback_xml = "\n<LEARNED_FEEDBACK>\n"
        for ex in corrected_examples:
            feedback_xml += f"  <case symbol=\"{ex['symbol_id']}\" verdict=\"FALSE_POSITIVE\">\n"
            if ex.get("comments"):
                feedback_xml += f"    <user_note>{ex['comments']}</user_note>\n"
            feedback_xml += "  </case>\n"
        feedback_xml += "</LEARNED_FEEDBACK>\n"

    retrieved_xml = []
    for r in retrieved:
        retrieved_xml.append(f"""
<dependent id="{r.chunk_id}" language="{r.language}">
  <name>{r.qualified_name}</name>
  <file>{r.file_path}</file>
  <coverage>{r.test_coverage_pct}</coverage>
  <risk_score>{r.risk_score_current}</risk_score>
  <code>
{r.content[:2000]} 
  </code>
</dependent>
""")
    
    cdl_xml = ""
    if cdl_delta:
        cdl_xml = f"""
<DETERMINISTIC_CONTRACT_DIFF is_breaking="{cdl_delta.is_breaking}" semver="{cdl_delta.semver_suggestion}">
  <changes>{[c.value for c in cdl_delta.changes]}</changes>
</DETERMINISTIC_CONTRACT_DIFF>
"""

    # Fix #8: Add a note when graph data is missing
    graph_available = bool(graph_summary.get("total_callers", 0) > 0 or graph_summary.get("nodes"))
    graph_note = ""
    if not graph_available:
        graph_note = (
            "\nNOTE: Graph database returned no data. "
            "Limit call graph claims to what is verifiable from the code context provided. "
            "Do not infer call chains that are not explicitly visible.\n"
        )

    user_content = f"""
<CHANGED_SYMBOL language="{changed_symbol.language}">
  <name>{changed_symbol.qualified_name}</name>
  <change_summary>{change_summary}</change_summary>
  <code>
{changed_symbol.content[:8000]}
  </code>
</CHANGED_SYMBOL>

{cdl_xml}

{feedback_xml}

<CALL_GRAPH_SUMMARY>
  Total Callers: {graph_summary.get("total_callers", 0)}
  Critical Callers: {graph_summary.get("critical_callers", 0)}
  Cycles: {graph_summary.get("cycles", [])}
</CALL_GRAPH_SUMMARY>
{graph_note}
<RETRIEVED_DEPENDENTS>
{"".join(retrieved_xml)}
</RETRIEVED_DEPENDENTS>
"""
    # Fix #5: Separate system and user roles
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]
