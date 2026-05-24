import os
import hashlib
import tree_sitter
import tree_sitter_python
from typing import List, Optional
from src.indexer.schema import CodeChunk

LANGUAGE = tree_sitter.Language(tree_sitter_python.language())
PARSER = tree_sitter.Parser(LANGUAGE)

def compute_chunk_id(qualified_name: str, file_path: str) -> str:
    return hashlib.sha256(f"{qualified_name}:{file_path}".encode("utf-8")).hexdigest()

def get_module_path(file_path: str, repo_root: str) -> str:
    rel_path = os.path.relpath(file_path, repo_root)
    # Remove .py extension and replace os.sep with .
    module_path = os.path.splitext(rel_path)[0].replace(os.sep, '.')
    return module_path

def get_node_text(node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8")

def extract_docstring(body_node, source_bytes: bytes) -> str:
    if not body_node:
        return ""
    if body_node.type == "block":
        first_child = body_node.children[0] if body_node.children else None
        if first_child and first_child.type == "expression_statement":
            string_node = first_child.children[0] if first_child.children else None
            if string_node and string_node.type == "string":
                return get_node_text(string_node, source_bytes)
    return ""

def calculate_complexity(node) -> int:
    complexity = 1
    # Simplified cyclomatic complexity
    complex_node_types = {"if_statement", "for_statement", "while_statement", "except_clause", "with_statement"}
    
    def walk(n):
        nonlocal complexity
        if n.type in complex_node_types:
            complexity += 1
        # count boolean operators 'and', 'or'
        if n.type == "boolean_operator":
            complexity += 1
        for child in n.children:
            walk(child)
            
    walk(node)
    return complexity

def parse_file(file_path: str, repo_root: str) -> List[CodeChunk]:
    with open(file_path, "rb") as f:
        source_bytes = f.read()
        
    tree = PARSER.parse(source_bytes)
    root_node = tree.root_node
    chunks = []
    
    module_path = get_module_path(file_path, repo_root)
    imports_text = []

    def process_function(node, parent_class_name=None):
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
            
        symbol_name = get_node_text(name_node, source_bytes)
        
        is_async = False
        if node.parent and node.parent.type == "async": # not technically correct for newer tree-sitter python but let's check both
            is_async = True
        # tree-sitter-python async functions: node itself might be function_definition, but check previous siblings or type
        
        # In tree-sitter-python, an async function might just be an async_function_definition node or decorated.
        # Wait, the node.parent could be async? No, there is usually `async` keyword child or different node type.
        # Tree-sitter-python doesn't use `async_function_definition` always, let's just check for 'async' keyword.
        for child in node.children:
            if child.type == "async":
                is_async = True
                break
                
        if node.type == "async_function_definition":
            is_async = True
        
        qualified_name = f"{module_path}.{symbol_name}"
        symbol_type = "function"
        if parent_class_name:
            qualified_name = f"{module_path}.{parent_class_name}.{symbol_name}"
            symbol_type = "method"
            
        parameters_node = node.child_by_field_name("parameters")
        signature = get_node_text(parameters_node, source_bytes) if parameters_node else "()"
        
        body_node = node.child_by_field_name("body")
        docstring = extract_docstring(body_node, source_bytes)
        complexity = calculate_complexity(body_node) if body_node else 1
        
        chunk = CodeChunk(
            symbol_name=symbol_name,
            qualified_name=qualified_name,
            file_path=file_path,
            language="python",
            symbol_type=symbol_type,
            signature=f"def {symbol_name}{signature}",
            is_async=is_async,
            docstring=docstring,
            complexity=complexity,
            chunk_id=compute_chunk_id(qualified_name, file_path)
        )
        chunks.append(chunk)

    def process_class(node):
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
            
        symbol_name = get_node_text(name_node, source_bytes)
        qualified_name = f"{module_path}.{symbol_name}"
        
        body_node = node.child_by_field_name("body")
        docstring = extract_docstring(body_node, source_bytes)
        
        chunk = CodeChunk(
            symbol_name=symbol_name,
            qualified_name=qualified_name,
            file_path=file_path,
            language="python",
            symbol_type="class",
            docstring=docstring,
            chunk_id=compute_chunk_id(qualified_name, file_path)
        )
        chunks.append(chunk)
        
        if body_node:
            for child in body_node.children:
                if child.type in ["function_definition", "async_function_definition"]:
                    process_function(child, parent_class_name=symbol_name)

    # Process all top-level nodes
    for child in root_node.children:
        if child.type in ["function_definition", "async_function_definition"]:
            process_function(child)
        elif child.type == "class_definition":
            process_class(child)
        elif child.type in ["import_statement", "import_from_statement"]:
            imports_text.append(get_node_text(child, source_bytes))

    # Add module-level import chunk
    if imports_text:
        chunk = CodeChunk(
            symbol_name="imports",
            qualified_name=f"{module_path}._imports",
            file_path=file_path,
            language="python",
            symbol_type="module",
            imports=imports_text,
            chunk_id=compute_chunk_id(f"{module_path}._imports", file_path)
        )
        chunks.append(chunk)

    return chunks
