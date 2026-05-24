from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict


class ParameterSchema(BaseModel):
    name: str
    type: Optional[str] = None
    default: Optional[str] = None
    required: bool = True


class RiskEvent(BaseModel):
    timestamp: str
    tier: str
    score: float
    reason: str


class SymbolChange(BaseModel):
    change_type: str
    summary: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None


class CodeChunk(BaseModel):
    model_config = {"extra": "allow"}  # F-4: Allow extra fields during transition period

    # Core Identity (8)
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    repo_id: str = Field(..., description="Repository identifier")
    file_path: str = Field(..., description="Relative path to the file")
    symbol_type: str = Field(..., description="Function, method, class, interface, etc.")
    symbol_name: str = Field(..., description="Local name of the symbol")
    qualified_name: str = Field(..., description="Fully qualified name including module/class")
    start_line: int = Field(..., description="1-indexed start line")
    end_line: int = Field(..., description="1-indexed end line")

    # Code Content (6)
    signature: str = Field(..., description="Function/method signature")
    docstring: Optional[str] = Field(None, description="Extracted docstring or comment")
    content: str = Field(..., description="Raw source code of the chunk")
    language: str = Field(..., description="Programming language")
    parameters: List[ParameterSchema] = Field(default_factory=list, description="Parsed parameters")
    return_type: Optional[str] = Field(None, description="Return type if specified")

    # Graph & Call info (3)
    calls: List[str] = Field(default_factory=list, description="Qualified names of symbols this chunk calls")
    called_by: List[str] = Field(default_factory=list, description="Qualified names of symbols that call this chunk")
    exceptions_raised: List[str] = Field(default_factory=list, description="Exceptions explicitly raised")

    # Modifiers & Flags (5)
    is_async: bool = Field(False, description="Whether the symbol is async")
    is_exported: bool = Field(False, description="Whether the symbol is exported/public")
    is_generated: bool = Field(False, description="Whether the file/code is auto-generated")
    is_on_critical_path: bool = Field(False, description="Whether the symbol is on a critical path")
    has_dynamic_dispatch: bool = Field(False, description="Whether the symbol uses dynamic dispatch")

    # Ownership & Context (4)
    service: Optional[str] = Field(None, description="Microservice name if applicable")
    team_owner: Optional[str] = Field(None, description="Team owning this symbol")
    api_surface: Optional[str] = Field(None, description="REST/GraphQL endpoint if applicable")
    contract_type: Optional[str] = Field(None, description="API contract definition")

    # Metrics & Risk (7)
    complexity: int = Field(0, description="Cyclomatic or AST depth complexity")
    churn_score: float = Field(0.0, description="Score based on modification frequency")
    test_coverage_pct: float = Field(0.0, description="Test coverage percentage (0.0 to 1.0)")
    fan_out: int = Field(0, description="Number of distinct external dependencies")
    break_count_90d: int = Field(0, description="Number of times this caused a break in last 90 days")
    last_modified: Optional[str] = Field(None, description="ISO datetime of last git modification")
    last_break_date: Optional[str] = Field(None, description="ISO datetime of last related incident")

    # Dynamic State (5)
    risk_score_current: float = Field(0.0, description="Current computed risk score")
    risk_score_history: List[RiskEvent] = Field(default_factory=list, description="History of risk score changes")
    commit_hash: Optional[str] = Field(None, description="Latest commit affecting this chunk")
    commit_message: Optional[str] = Field(None, description="Latest commit message")
    author: Optional[str] = Field(None, description="Author of the latest modification")

    # Diff & Analysis (6)
    change_summary: Optional[str] = Field(None, description="AI or heuristics generated summary of change")
    diff_changes: List[SymbolChange] = Field(default_factory=list, description="Structured diff parsed elements")
    embedding_text: Optional[str] = Field(None, description="The concatenated string used for vector embedding")
    dead_code_verdict: Optional[str] = Field(None, description="dead, dynamic, entry_point, unknown")
    file_hash: Optional[str] = Field(None, description="SHA-256 hash of the file at time of indexing")
    contract_data: Optional[Dict[str, Any]] = Field(None, description="Deterministic CDL contract data")

    # Fix #6: Embedding vector as a typed field instead of dynamic _embedding_vector
    embedding_vector: Optional[List[float]] = Field(None, description="Set after embed_chunks() is called. None means not yet embedded.")
