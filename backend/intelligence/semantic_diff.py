from typing import List, Optional
from backend.indexer.schema import CodeChunk, SymbolChange

class SemanticDiffParser:
    """
    Parses a git diff to extract structural changes per symbol.
    Returns list[SymbolChange] with auto-generated change_summary strings.
    No LLM required — all summaries are deterministic from AST comparison.
    """
    CHANGE_TEMPLATES = {
        "param_added_required":
            "New required parameter `{name}: {type}` added to `{symbol}` — all callers must pass this argument.",
        "param_removed":
            "Parameter `{name}` removed from `{symbol}` — callers passing this argument will raise TypeError.",
        "return_type_changed":
            "Return type changed from `{old}` to `{new}` — callers assuming `{old}` will fail at runtime.",
        "exception_added":
            "New exception `{exc}` may be raised — callers without try/except will crash.",
        "async_added":
            "`{symbol}` is now async — all callers must be awaited.",
        "async_removed":
            "`{symbol}` is no longer async — all await call sites will raise SyntaxError.",
        "deleted":
            "`{symbol}` was deleted — all callers will raise ImportError or AttributeError.",
        "logic_changed":
            "Internal logic changed in `{symbol}` — behavioural regression possible in dependent tests.",
    }

    def parse_diff(self, old_chunk: Optional[CodeChunk], new_chunk: Optional[CodeChunk]) -> List[SymbolChange]:
        changes = []
        
        # 1. Deleted
        if old_chunk and not new_chunk:
            changes.append(SymbolChange(
                change_type="deleted",
                summary=self.CHANGE_TEMPLATES["deleted"].format(symbol=old_chunk.qualified_name)
            ))
            return changes
            
        # 2. Created (not strictly a diff breaking change for existing dependents, but worth noting)
        if not old_chunk and new_chunk:
            return []
            
        symbol = new_chunk.qualified_name
        
        # 3. Async changes
        if not old_chunk.is_async and new_chunk.is_async:
            changes.append(SymbolChange(
                change_type="async_added",
                summary=self.CHANGE_TEMPLATES["async_added"].format(symbol=symbol)
            ))
        elif old_chunk.is_async and not new_chunk.is_async:
            changes.append(SymbolChange(
                change_type="async_removed",
                summary=self.CHANGE_TEMPLATES["async_removed"].format(symbol=symbol)
            ))
            
        # 4. Return type changed
        if old_chunk.return_type != new_chunk.return_type:
            changes.append(SymbolChange(
                change_type="return_type_changed",
                summary=self.CHANGE_TEMPLATES["return_type_changed"].format(
                    old=old_chunk.return_type or "any",
                    new=new_chunk.return_type or "any"
                ),
                old_value=old_chunk.return_type,
                new_value=new_chunk.return_type
            ))
            
        # 5. Parameters changed
        old_params = {p.name: p for p in old_chunk.parameters}
        new_params = {p.name: p for p in new_chunk.parameters}
        
        for name, param in new_params.items():
            if name not in old_params and param.required:
                changes.append(SymbolChange(
                    change_type="param_added_required",
                    summary=self.CHANGE_TEMPLATES["param_added_required"].format(
                        name=name, type=param.type or "any", symbol=symbol
                    )
                ))
                
        for name in old_params:
            if name not in new_params:
                changes.append(SymbolChange(
                    change_type="param_removed",
                    summary=self.CHANGE_TEMPLATES["param_removed"].format(name=name, symbol=symbol)
                ))
                
        # 6. Exceptions added
        old_exc = set(old_chunk.exceptions_raised)
        new_exc = set(new_chunk.exceptions_raised)
        for exc in new_exc - old_exc:
            changes.append(SymbolChange(
                change_type="exception_added",
                summary=self.CHANGE_TEMPLATES["exception_added"].format(exc=exc)
            ))
            
        # 7. Fallback to logic changed if content changed but signature didn't
        if not changes and old_chunk.content != new_chunk.content:
            changes.append(SymbolChange(
                change_type="logic_changed",
                summary=self.CHANGE_TEMPLATES["logic_changed"].format(symbol=symbol)
            ))
            
        return changes
