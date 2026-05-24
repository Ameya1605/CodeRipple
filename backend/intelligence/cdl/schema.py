from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional

class BreakingChangeType(Enum):
    PARAM_ADDED_REQUIRED = "param_added_required"
    PARAM_REMOVED = "param_removed"
    PARAM_TYPE_NARROWED = "param_type_narrowed"
    RETURN_TYPE_CHANGED = "return_type_changed"
    RETURN_TYPE_NARROWED = "return_type_narrowed"
    EXCEPTION_ADDED = "exception_added"
    EXCEPTION_REMOVED = "exception_removed"
    SIDE_EFFECT_ADDED = "side_effect_added"
    VISIBILITY_REDUCED = "visibility_reduced"  # public → private/protected
    ASYNC_CHANGED = "async_changed"            # sync ↔ async
    SEMVER_SUGGESTION = "semver_suggestion"

@dataclass
class SymbolContract:
    qualified_name: str
    parameters: List[dict] = field(default_factory=list) # [{name, type, required, default}]
    return_type: Optional[str] = None
    raises: List[str] = field(default_factory=list)      # exception type names
    side_effects: List[str] = field(default_factory=list) # ["writes_db", "reads_env", "network_call"]
    is_async: bool = False
    visibility: str = "public"                            # public | protected | private
    performance_sla_ms: Optional[int] = None              # extracted from docstring annotations

@dataclass
class ContractDelta:
    symbol: str
    changes: List[BreakingChangeType]
    old_contract: Optional[SymbolContract]
    new_contract: SymbolContract
    is_breaking: bool
    semver_suggestion: str             # "major" | "minor" | "patch"
    explanation: str = ""              # LLM-generated rationale
