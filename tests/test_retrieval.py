import pytest
from unittest.mock import AsyncMock, patch
from backend.indexer.schema import CodeChunk
from backend.retrieval.retriever import retrieve_dependents

@pytest.fixture
def mock_chunk():
    return CodeChunk(
        chunk_id="1", repo_id="r1", file_path="f.py", symbol_type="func",
        symbol_name="f", qualified_name="f", start_line=1, end_line=2,
        signature="def f()", content="pass", language="python",
        risk_score_current=0.5
    )

@pytest.mark.asyncio
@patch('backend.retrieval.retriever.embed_chunks', new_callable=AsyncMock)
@patch('backend.retrieval.retriever.vector_store.search', new_callable=AsyncMock)
@patch('backend.retrieval.retriever.neo4j_client.session')
async def test_retrieve_dependents_ranking(mock_session, mock_search, mock_embed, mock_chunk):
    # Mock embedding vector population
    async def side_effect(chunks):
        for c in chunks:
            c._embedding_vector = [0.1] * 1536
        return chunks
    mock_embed.side_effect = side_effect
    
    # Mock vector results (Phase A)
    v_chunk = mock_chunk.model_copy(update={"chunk_id": "2", "qualified_name": "v_caller", "risk_score_current": 0.2})
    mock_search.return_value = [{"id": "2", "score": 0.8, "payload": v_chunk.model_dump()}]
    
    # Mock neo4j session (Phase B)
    class MockResult:
        def __init__(self, data_list): self.data_list = data_list
        async def data(self): return self.data_list
        
    class MockSession:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        async def run(self, query, **kwargs):
            if "apoc.path.subgraphNodes" in query: # BLAST_RADIUS
                g_chunk = mock_chunk.model_copy(update={"chunk_id": "3", "qualified_name": "g_caller", "risk_score_current": 0.8})
                return MockResult([{"node": g_chunk.model_dump(), "depth": 1}])
            return MockResult([]) # Empty for CRITICAL_CALLERS
            
    mock_session.return_value = MockSession()
    
    results = await retrieve_dependents(mock_chunk)
    
    assert len(results) == 2
    names = [r.qualified_name for r in results]
    assert "g_caller" in names
    assert "v_caller" in names
    
    # Expected Ranking calculation:
    # RERANK_VECTOR_W = 0.60
    # RERANK_GRAPH_W  = 0.25
    # RERANK_RISK_W   = 0.15
    #
    # g_caller: v_score=0.0, depth=1 -> graph_score=1.0. 
    # final_score = 0*0.60 + 1*0.25 + 0.8*0.15 = 0.25 + 0.12 = 0.37
    # v_caller: v_score=0.8, depth=99 -> graph_score=1/99=0.0101
    # final_score = 0.8*0.60 + 0.0101*0.25 + 0.2*0.15 = 0.48 + 0.0025 + 0.03 = 0.5125
    
    # So v_caller should rank higher than g_caller.
    assert results[0].qualified_name == "v_caller"
    assert results[1].qualified_name == "g_caller"
