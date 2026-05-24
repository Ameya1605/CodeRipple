import os
import pytest
import networkx as nx
from src.indexer.ast_parser import parse_file
from src.indexer.call_graph import build_call_graph, get_blast_radius

FIXTURE_PATH = "tests/fixtures/sample_graph.py"

@pytest.fixture(autouse=True)
def setup_fixture():
    os.makedirs("tests/fixtures", exist_ok=True)
    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        f.write('''def func_a():
    pass

def func_b():
    func_a()

def func_c():
    func_b()

def func_d():
    func_c()
''')
    yield
    if os.path.exists(FIXTURE_PATH):
        os.remove(FIXTURE_PATH)

def test_call_graph_builder():
    chunks = parse_file(FIXTURE_PATH, ".")
    graph = build_call_graph(chunks, ".")
    
    # Node existence
    qnames = [c.qualified_name for c in chunks if c.symbol_type == "function"]
    for qn in qnames:
        assert qn in graph.nodes
        
    # Edge A <- B <- C <- D
    a_qname = "tests.fixtures.sample_graph.func_a"
    b_qname = "tests.fixtures.sample_graph.func_b"
    c_qname = "tests.fixtures.sample_graph.func_c"
    d_qname = "tests.fixtures.sample_graph.func_d"
    
    assert graph.has_edge(b_qname, a_qname)
    assert graph.has_edge(c_qname, b_qname)
    assert graph.has_edge(d_qname, c_qname)
    
    # called_by
    chunk_a = next(c for c in chunks if c.qualified_name == a_qname)
    assert b_qname in chunk_a.called_by
    
    # blast radius (following incoming edges = who calls me)
    blast = get_blast_radius(graph, a_qname, max_depth=3)
    assert b_qname in blast["direct"]
    assert c_qname in blast["depth_2"]
    assert d_qname in blast["depth_3"]
