import pytest
from backend.intelligence.semantic_diff import SemanticDiffParser
from backend.indexer.schema import CodeChunk, ParameterSchema

def create_mock_chunk(signature, params, return_type, exceptions, is_async, content):
    return CodeChunk(
        chunk_id="1", repo_id="repo1", file_path="f.py", symbol_type="func",
        symbol_name="f", qualified_name="f", start_line=1, end_line=5,
        signature=signature, content=content, language="python",
        parameters=params, return_type=return_type,
        exceptions_raised=exceptions, is_async=is_async
    )

def test_semantic_diff_cases():
    parser = SemanticDiffParser()
    
    # 1. Deleted
    old = create_mock_chunk("def f()", [], None, [], False, "pass")
    changes = parser.parse_diff(old, None)
    assert len(changes) == 1
    assert changes[0].change_type == "deleted"
    
    # 2. Async added
    new = create_mock_chunk("async def f()", [], None, [], True, "pass")
    changes = parser.parse_diff(old, new)
    assert len(changes) == 1
    assert changes[0].change_type == "async_added"
    
    # 3. Return type changed
    new = create_mock_chunk("def f() -> int", [], "int", [], False, "pass")
    changes = parser.parse_diff(old, new)
    assert len(changes) == 1
    assert changes[0].change_type == "return_type_changed"
    
    # 4. Param added required
    params = [ParameterSchema(name="a", type="int", required=True)]
    new = create_mock_chunk("def f(a: int)", params, None, [], False, "pass")
    changes = parser.parse_diff(old, new)
    assert len(changes) == 1
    assert changes[0].change_type == "param_added_required"
    
    # 5. Param removed
    changes = parser.parse_diff(new, old)
    assert len(changes) == 1
    assert changes[0].change_type == "param_removed"
    
    # 6. Exception added
    new = create_mock_chunk("def f()", [], None, ["ValueError"], False, "pass")
    changes = parser.parse_diff(old, new)
    assert len(changes) == 1
    assert changes[0].change_type == "exception_added"
    
    # 7. Logic changed (content differs, but signature same)
    new = create_mock_chunk("def f()", [], None, [], False, "print('hello')")
    changes = parser.parse_diff(old, new)
    assert len(changes) == 1
    assert changes[0].change_type == "logic_changed"
    
    # 8. Async removed
    old_async = create_mock_chunk("async def f()", [], None, [], True, "pass")
    changes = parser.parse_diff(old_async, old)
    assert len(changes) == 1
    assert changes[0].change_type == "async_removed"

    # 9. Multiple changes (Param added, return type changed)
    new_complex = create_mock_chunk("def f(a: int) -> str", params, "str", [], False, "pass")
    changes = parser.parse_diff(old, new_complex)
    assert len(changes) == 2
    types = [c.change_type for c in changes]
    assert "param_added_required" in types
    assert "return_type_changed" in types
    
    # 10. No changes
    changes = parser.parse_diff(old, old)
    assert len(changes) == 0
