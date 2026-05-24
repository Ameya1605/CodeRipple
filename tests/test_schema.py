import pytest
from backend.indexer.schema import CodeChunk, ParameterSchema, RiskEvent, SymbolChange

def test_code_chunk_schema():
    chunk = CodeChunk(
        chunk_id="123",
        repo_id="test-repo",
        file_path="src/main.py",
        symbol_type="function",
        symbol_name="do_work",
        qualified_name="src.main.do_work",
        start_line=10,
        end_line=20,
        signature="def do_work(a: int) -> str",
        content="def do_work(a: int):\n    return str(a)",
        language="python"
    )

    assert chunk.chunk_id == "123"
    assert chunk.is_async is False
    assert chunk.complexity == 0
    assert chunk.risk_score_current == 0.0

    # Add missing fields to check optional functionality
    chunk.parameters.append(ParameterSchema(name="a", type="int"))
    chunk.risk_score_history.append(RiskEvent(timestamp="2023-01-01T00:00:00Z", tier="HIGH", score=0.8, reason="foo"))
    chunk.diff_changes.append(SymbolChange(change_type="param_added", summary="Added param"))

    assert len(chunk.parameters) == 1
    assert chunk.parameters[0].name == "a"
    assert len(chunk.risk_score_history) == 1
    assert chunk.risk_score_history[0].tier == "HIGH"
    assert len(chunk.diff_changes) == 1
    assert chunk.diff_changes[0].change_type == "param_added"
