from typing import Literal, List, Dict
from pydantic import BaseModel, Field

class CodeChunk(BaseModel):
    symbol_name: str
    qualified_name: str
    file_path: str
    language: str
    symbol_type: Literal["function", "method", "class", "module", "export"]
    signature: str = ""
    parameters: List[Dict] = Field(default_factory=list)
    return_type: str = ""
    is_async: bool = False
    is_exported: bool = False
    docstring: str = ""
    inline_comments: str = ""
    calls: List[str] = Field(default_factory=list)
    called_by: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    imported_by: List[str] = Field(default_factory=list)
    overrides: str = ""
    test_coverage: List[str] = Field(default_factory=list)
    team_owner: str = ""
    service: str = ""
    last_modified: str = ""
    churn_score: float = 0.0
    complexity: int = 0
    embedding_text: str = ""
    chunk_id: str
    embedding_model_version: str = ""
    is_critical_path: bool = False
    has_dynamic_dispatch: bool = False
    is_generated: bool = False
    is_external: bool = False
    external_repo: str = ""
