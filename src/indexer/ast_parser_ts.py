import os
import tree_sitter
import tree_sitter_typescript
from typing import List
from src.indexer.schema import CodeChunk
from src.indexer.ast_parser import compute_chunk_id

LANGUAGE_TS = tree_sitter.Language(tree_sitter_typescript.language_typescript())
PARSER_TS = tree_sitter.Parser()
PARSER_TS.set_language(LANGUAGE_TS)

def get_node_text(node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8")

def parse_file_ts(file_path: str, repo_root: str) -> List[CodeChunk]:
    with open(file_path, "rb") as f:
        source_bytes = f.read()
        
    tree = PARSER_TS.parse(source_bytes)
    root_node = tree.root_node
    chunks = []
    
    module_path = os.path.relpath(file_path, repo_root).replace(os.sep, '/')
    
    def process_node(node):
        is_exported = False
        if node.parent and node.parent.type == "export_statement":
            is_exported = True
            
        if node.type in ["function_declaration", "arrow_function"]:
            name_node = node.child_by_field_name("name")
            if not name_node and node.type == "arrow_function" and node.parent.type == "variable_declarator":
                name_node = node.parent.child_by_field_name("name")
                
            if name_node:
                symbol_name = get_node_text(name_node, source_bytes)
                qname = f"{module_path}:{symbol_name}"
                
                chunk = CodeChunk(
                    symbol_name=symbol_name,
                    qualified_name=qname,
                    file_path=file_path,
                    language="typescript",
                    symbol_type="function",
                    is_exported=is_exported,
                    chunk_id=compute_chunk_id(qname, file_path)
                )
                chunks.append(chunk)
                
        elif node.type in ["class_declaration", "interface_declaration", "type_alias_declaration"]:
            name_node = node.child_by_field_name("name")
            if name_node:
                symbol_name = get_node_text(name_node, source_bytes)
                qname = f"{module_path}:{symbol_name}"
                docstring = "interface" if node.type == "interface_declaration" else ""
                
                chunk = CodeChunk(
                    symbol_name=symbol_name,
                    qualified_name=qname,
                    file_path=file_path,
                    language="typescript",
                    symbol_type="class",
                    is_exported=is_exported,
                    docstring=docstring,
                    chunk_id=compute_chunk_id(qname, file_path)
                )
                chunks.append(chunk)

        for child in node.children:
            process_node(child)
            
    process_node(root_node)
    return chunks
