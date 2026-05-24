import os
import pytest
try:
    from backend.indexer.parsers.parser_py import parse_python_file
    from backend.indexer.parsers.parser_ts import parse_ts_file
    from backend.indexer.parsers.parser_go import parse_go_file
    from backend.indexer.parsers.parser_rust import parse_rust_file
    from backend.indexer.parsers.parser_java import parse_java_file
except ImportError:
    parse_python_file = None
    parse_ts_file = None
    parse_go_file = None
    parse_rust_file = None
    parse_java_file = None

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

@pytest.fixture(autouse=True)
def setup_fixtures():
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    
    with open(os.path.join(FIXTURES_DIR, "sample.py"), "w") as f:
        f.write("class MyClass:\n    def my_method(self, arg1: int):\n        pass\n\nasync def my_func():\n    pass")
    
    with open(os.path.join(FIXTURES_DIR, "sample.ts"), "w") as f:
        f.write("export class MyTsClass {\n  myMethod(arg1: number) {}\n}\nexport async function myTsFunc() {}")
        
    with open(os.path.join(FIXTURES_DIR, "sample.go"), "w") as f:
        f.write("package main\ntype MyStruct struct {}\nfunc (m *MyStruct) MyMethod(arg1 int) {}\nfunc MyFunc() {}")
        
    with open(os.path.join(FIXTURES_DIR, "sample.rs"), "w") as f:
        f.write("pub struct MyStruct;\nimpl MyStruct {\n    pub fn my_method(&self, arg1: i32) {}\n}\npub async fn my_func() {}")
        
    with open(os.path.join(FIXTURES_DIR, "sample.java"), "w") as f:
        f.write("public class MyClass {\n    public void myMethod(int arg1) {}\n}")

def test_parse_python_file():
    if not parse_python_file: pytest.skip("tree-sitter bindings not installed")
    chunks = parse_python_file(os.path.join(FIXTURES_DIR, "sample.py"), "repo1")
    assert len(chunks) == 3 # MyClass, my_method, my_func
    names = [c.symbol_name for c in chunks]
    assert "MyClass" in names
    assert "my_method" in names
    assert "my_func" in names

def test_parse_ts_file():
    if not parse_ts_file: pytest.skip("tree-sitter bindings not installed")
    chunks = parse_ts_file(os.path.join(FIXTURES_DIR, "sample.ts"), "repo1")
    assert len(chunks) == 3 # MyTsClass, myMethod, myTsFunc
    names = [c.symbol_name for c in chunks]
    assert "MyTsClass" in names
    assert "myMethod" in names
    assert "myTsFunc" in names

def test_parse_go_file():
    if not parse_go_file: pytest.skip("tree-sitter bindings not installed")
    chunks = parse_go_file(os.path.join(FIXTURES_DIR, "sample.go"), "repo1")
    assert len(chunks) == 3 # MyStruct, MyMethod, MyFunc
    names = [c.symbol_name for c in chunks]
    assert "MyStruct" in names
    assert "MyMethod" in names
    assert "MyFunc" in names

def test_parse_rust_file():
    if not parse_rust_file: pytest.skip("tree-sitter bindings not installed")
    chunks = parse_rust_file(os.path.join(FIXTURES_DIR, "sample.rs"), "repo1")
    assert len(chunks) == 3 # MyStruct, my_method, my_func
    names = [c.symbol_name for c in chunks]
    assert "MyStruct" in names
    assert "my_method" in names
    assert "my_func" in names

def test_parse_java_file():
    if not parse_java_file: pytest.skip("tree-sitter bindings not installed")
    chunks = parse_java_file(os.path.join(FIXTURES_DIR, "sample.java"), "repo1")
    assert len(chunks) == 2 # MyClass, myMethod
    names = [c.symbol_name for c in chunks]
    assert "MyClass" in names
    assert "myMethod" in names
