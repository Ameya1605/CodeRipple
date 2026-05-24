import os
import pytest
from src.indexer.ast_parser import parse_file

FIXTURE_PATH = "tests/fixtures/sample.py"

@pytest.fixture(autouse=True)
def setup_fixture():
    os.makedirs("tests/fixtures", exist_ok=True)
    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        f.write('''import os
from typing import List

def top_level_func(a: int) -> int:
    """This is a docstring"""
    if a > 0:
        return a
    return 0

async def my_async_func():
    pass

class MyClass:
    """Class docstring"""
    
    def __init__(self, name):
        self.name = name
        
    def do_something(self):
        for i in range(10):
            print(i)
''')
    yield
    if os.path.exists(FIXTURE_PATH):
        try:
            os.remove(FIXTURE_PATH)
        except Exception:
            pass

def test_parse_file():
    repo_root = "."
    chunks = parse_file(FIXTURE_PATH, repo_root)
    
    assert len(chunks) == 6 # module imports, top_level_func, my_async_func, MyClass, MyClass.__init__, MyClass.do_something
    
    module_chunk = next(c for c in chunks if c.symbol_type == "module")
    assert len(module_chunk.imports) == 2
    
    tl_func = next(c for c in chunks if c.symbol_name == "top_level_func")
    assert tl_func.symbol_type == "function"
    assert "This is a docstring" in tl_func.docstring
    assert not tl_func.is_async
    assert tl_func.complexity >= 2 # 1 + 1 for 'if'
    
    async_func = next(c for c in chunks if c.symbol_name == "my_async_func")
    assert async_func.is_async
    
    cls_chunk = next(c for c in chunks if c.symbol_name == "MyClass")
    assert cls_chunk.symbol_type == "class"
    
    init_method = next(c for c in chunks if c.symbol_name == "__init__")
    assert init_method.symbol_type == "method"
    assert init_method.qualified_name == "tests.fixtures.sample.MyClass.__init__"
